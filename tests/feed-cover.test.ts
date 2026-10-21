import { describe, expect, test } from 'bun:test';
import { extractFeedCover, extractFeedCovers } from '../scripts/feed-cover';
import { parseFeed } from '../scripts/generate-readme';
import { mkdtempSync, mkdirSync, cpSync, writeFileSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';

describe('当期 RSS 配图', () => {
  test('定时生成器将当期配图写入可解析的 README.json 元数据', async () => {
    const directory = mkdtempSync(join(tmpdir(), 'weekly-cover-test-'));
    try {
      mkdirSync(join(directory, 'items/AI'), { recursive: true });
      cpSync(resolve(import.meta.dir, '../template'), join(directory, 'template'), { recursive: true, filter: source => !source.includes('/template/site') });
      writeFileSync(join(directory, 'items/AI/fixture.yaml'), 'kind: AI\nowner: Tester\nname: 测试周刊\nlink: https://example.com\ndesc: 测试\nfeed_url: https://example.com/rss\n');
      const coverUrl = 'https://example.com/cover.png?a=1&label="test"';
      writeFileSync(join(directory, '.feed-cache.json'), JSON.stringify({ 'https://example.com/rss': {
        latestTitle: '当期文章', latestLink: 'https://example.com/issue', publishedDate: '2026-10-21T00:00:00Z', coverUrl, coverUrls: [coverUrl, 'https://example.com/backup.jpg'], fetchedAt: Date.now(),
      } }));
      const process = Bun.spawn([Bun.which('bun')!, resolve(import.meta.dir, '../scripts/generate-readme.ts')], { cwd: directory, stdout: 'pipe', stderr: 'pipe' });
      const [code, output, errors] = await Promise.all([process.exited, new Response(process.stdout).text(), new Response(process.stderr).text()]);
      expect(code, output + errors).toBe(0);
      const metadata = JSON.parse(readFileSync(join(directory, 'README.json'), 'utf8'));
      expect(metadata[0].feeds[0].cover_url).toBe(coverUrl);
      expect(metadata[0].feeds[0].cover_urls).toEqual([coverUrl, 'https://example.com/backup.jpg']);
      expect(metadata[0].feeds[0].latest_post).toContain('https://example.com/issue');
    } finally { rmSync(directory, { recursive: true, force: true }); }
  });

  test('条目顺序与日期不一致时，图片仍与最新一期文章对应', async () => {
    const xml = `<rss version="2.0"><channel><title>周刊</title><link>https://example.com</link>
      <image><url>https://example.com/channel.jpg</url></image>
      <item><title>旧一期</title><link>https://example.com/old</link><pubDate>20 Oct 2026 00:00:00 GMT</pubDate><enclosure url="https://example.com/old.jpg" type="image/jpeg" length="1000"/></item>
      <item><title>新一期</title><link>https://example.com/new</link><pubDate>21 Oct 2026 00:00:00 GMT</pubDate><enclosure url="https://example.com/new.jpg" type="image/jpeg" length="1000"/></item>
      </channel></rss>`;
    const result = await parseFeed('https://example.com/rss', xml, 'https://example.com');
    expect(result.latestLink).toBe('https://example.com/new');
    expect(result.coverUrl).toBe('https://example.com/new.jpg');
  });

  test('Media RSS 分组中的缩略图可作为当期配图', async () => {
    const xml = `<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/"><channel><title>周刊</title>
      <item><title>一期</title><link>https://example.com/issue</link><media:group><media:thumbnail url="/cover.jpg"/></media:group></item>
      </channel></rss>`;
    expect((await parseFeed('https://example.com/rss', xml, 'https://example.com')).coverUrl).toBe('https://example.com/cover.jpg');
  });

  test('没有专用配图时，从正文跳过追踪像素和头像并解析懒加载相对地址', async () => {
    expect(await extractFeedCover({ content: '<img width="1" height="1" src="/counter"><img src="/avatar.jpg"><img alt="logo" src="/person.jpg"><img data-src="../photo.jpg?a=1&amp;b=2">' }, 'https://example.com/posts/issue'))
      .toBe('https://example.com/photo.jpg?a=1&b=2');
  });

  test('存在图片附件时优先使用附件，视频附件不作为图片', async () => {
    const item = { enclosure: { type: 'image/jpeg', url: '/cover.jpg' }, content: '<img src="/body.jpg">' };
    expect(await extractFeedCover(item, 'https://example.com')).toBe('https://example.com/cover.jpg');
    item.enclosure.type = 'video/mp4';
    expect(await extractFeedCover(item, 'https://example.com')).toBe('https://example.com/body.jpg');
  });

  test('条目没有图片或只含不可用协议时，返回空值以交给网页配图兜底', async () => {
    expect(await extractFeedCover({}, 'https://example.com')).toBe('');
    expect(await extractFeedCover({ content: '<img src="javascript:alert(1)"><img src="data:image/png;base64,abc">' }, 'https://example.com')).toBe('');
  });

  test('RSS 中多个媒体附件与正文图片都保留，便于首图失效后继续尝试', async () => {
    const xml = `<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/"><channel><title>周刊</title><item><title>一期</title><link>https://example.com/issue</link><media:content url="/one.jpg" type="image/jpeg"/><media:content url="/video.mp4" type="video/mp4"/><media:content url="/two.jpg" type="image/jpeg"/><description><![CDATA[<img src="/body.jpg">]]></description></item></channel></rss>`;
    expect((await parseFeed('https://example.com/rss', xml, 'https://example.com')).coverUrls)
      .toEqual(['https://example.com/one.jpg', 'https://example.com/two.jpg', 'https://example.com/body.jpg']);
  });

  test('Atom 的图片附件可提取，普通文章链接不会被当成图片', async () => {
    const xml = `<feed xmlns="http://www.w3.org/2005/Atom"><title>周刊</title><entry><title>一期</title><link rel="alternate" href="https://example.com/issue"/><link rel="enclosure" type="image/jpeg" href="https://example.com/cover.jpg"/></entry></feed>`;
    const result = await parseFeed('https://example.com/atom', xml, 'https://example.com');
    expect(result.latestLink).toBe('https://example.com/issue');
    expect(result.coverUrls).toEqual(['https://example.com/cover.jpg']);
  });

  test('正文只有纯文本时仍检查摘要中的懒加载图片和响应式候选', async () => {
    const result = await extractFeedCovers({content: '正文摘录', description: '<picture><source srcset="/small.webp 400w, /large.webp 1200w"><img width="1" height="1" data-original="/real.jpg" src="data:image/gif;base64,AA"></picture>'}, 'https://example.com/post');
    expect(result).toEqual(['https://example.com/large.webp', 'https://example.com/small.webp', 'https://example.com/real.jpg']);
  });

  test('CDN 图片地址包含逗号时不会被错误拆成多个地址', async () => {
    expect(await extractFeedCover({content: '<img srcset="https://cdn.example.com/w_400,q_80/a.jpg 400w, https://cdn.example.com/w_1200,q_80/a.jpg 1200w">'}, 'https://example.com'))
      .toBe('https://cdn.example.com/w_1200,q_80/a.jpg');
  });
});
