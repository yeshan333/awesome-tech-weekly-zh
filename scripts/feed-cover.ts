/** Extract issue-specific images; channel logos are never article covers. */
import { decodeHTML } from 'entities';

export function imageURL(value: unknown, base: string): string {
  if (typeof value !== 'string' || !value.trim()) return '';
  try {
    const url = new URL(decodeHTML(value), base);
    if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password) return '';
    if (/(?:avatar|favicon|tracking|pixel|badge|logo|qr[-_]|qrcode|\/profile\.)/i.test(url.host + url.pathname)) return '';
    return url.href;
  } catch { return ''; }
}

function srcsetURLs(value: string): string[] {
  const candidates: { url: string; size: number }[] = [];
  let remaining = value.trim();
  while (remaining) {
    remaining = remaining.replace(/^[,\s]+/, '');
    const match = remaining.match(/^\S+/);
    if (!match) break;
    let url = match[0];
    remaining = remaining.slice(url.length);
    let descriptor = '';
    if (url.endsWith(',')) url = url.replace(/,+$/, '');
    else {
      const end = remaining.indexOf(',');
      descriptor = end === -1 ? remaining : remaining.slice(0, end);
      remaining = end === -1 ? '' : remaining.slice(end + 1);
    }
    const dimension = descriptor.match(/^\s*(\d+(?:\.\d+)?)([wx])\s*$/);
    if (!descriptor.trim() || dimension) candidates.push({ url, size: dimension ? Number(dimension[1]) * (dimension[2] === 'x' ? 800 : 1) : 800 });
  }
  return candidates.sort((a, b) => Number(a.size > 1600) - Number(b.size > 1600) || (a.size > 1600 ? a.size - b.size : b.size - a.size)).map(item => item.url);
}

export async function extractFeedCovers(item: Record<string, any>, base: string): Promise<string[]> {
  const images: string[] = [];
  const add = (value: unknown) => {
    const url = imageURL(value, base);
    if (url && !images.includes(url) && images.length < 12) images.push(url);
  };
  function media(value: any) {
    if (Array.isArray(value)) { value.forEach(media); return; }
    const attrs = value?.$ || value;
    if (!attrs || typeof attrs !== 'object') return;
    if (attrs.type && !String(attrs.type).startsWith('image/')) return;
    if (attrs.medium && attrs.medium !== 'image') return;
    add(attrs.url || attrs.href);
  }
  if (item.enclosure?.type?.startsWith('image/')) media(item.enclosure);
  for (const key of ['imageEnclosures', 'media:content', 'media:thumbnail']) media(item[key]);
  const groups = item['media:group'];
  for (const group of Array.isArray(groups) ? groups : [groups]) {
    media(group?.['media:content']); media(group?.['media:thumbnail']);
  }
  for (const link of item.atomLinks || []) {
    if (link?.$?.rel === 'enclosure' && link.$.type?.startsWith('image/')) media(link);
  }
  const bodies = [item['content:encoded'], item.content, item.description, item.summary].map(value => typeof value === 'string' ? value : value?._).filter(value => typeof value === 'string');
  for (const markup of new Set(bodies)) {
    await new HTMLRewriter().on('img, picture source', { element(element) {
      const get = (attr: string) => element.getAttribute(attr) || '';
      const hint = ['alt', 'class', 'id', 'aria-label'].map(get).join(' ');
      if (/(?:avatar|logo|profile|author|qrcode|二维码)/i.test(hint)) return;
      const lazy = ['data-original', 'data-lazy-src', 'data-src', 'data-srcset', 'srcset'].some(attr => get(attr));
      const width = Number(get('width')), height = Number(get('height'));
      if (!lazy && ((width > 0 && width < 160) || (height > 0 && height < 90))) return;
      for (const attr of ['data-original', 'data-lazy-src', 'data-src']) add(get(attr));
      for (const attr of ['data-srcset', 'srcset']) srcsetURLs(get(attr)).forEach(add);
      add(get('src'));
    } }).transform(new Response(markup)).text();
  }
  return images;
}

export async function extractFeedCover(item: Record<string, any>, base: string): Promise<string> {
  return (await extractFeedCovers(item, base))[0] || '';
}
