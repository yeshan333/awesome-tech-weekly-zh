import { existsSync, readFileSync, writeFileSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { Glob } from 'bun';
import * as YAML from 'yaml';
import Parser from 'rss-parser';

// NOTE: We globally disable TLS verification to allow fetching feeds from personal/legacy developer blogs 
// that might use self-signed or expired SSL certificates. This is acceptable here as this script only 
// reads public RSS/Atom XML data and does not transmit any user credentials or sensitive APIs.
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

// Configuration
const CACHE_FILE = '.feed-cache.json';
const CACHE_DURATION_MS = 6 * 60 * 60 * 1000; // 6 hours
const CONCURRENCY_LIMIT = 5;
const FETCH_TIMEOUT_MS = 15000; // 15 seconds
const FETCH_RETRIES = 2;

const DEFAULT_JOBS = [
  { template: 'template/README.tpl', output: 'README.md' },
  { template: 'template/README-en.tpl', output: 'resources/README-en.md' },
  { template: 'template/README.json.tpl', output: 'README.json' },
  { template: 'template/README.yaml.tpl', output: 'README.yaml' }
];

// CLI Arguments
const forceFetch = process.argv.includes('--force');

interface YamlItem {
  kind: string;
  owner: string;
  name: string;
  link: string;
  desc: string;
  desc_en?: string;
  feed_url?: string;
  filePath: string;
}

interface FeedInfo {
  latestTitle: string;
  latestLink: string;
  publishedDate: string;
  fetchedAt: number;
}

interface Group {
  key: string;
  val: YamlItem[];
}

// Global Feed Cache
let feedCache: Record<string, FeedInfo> = {};

function loadCache() {
  if (existsSync(CACHE_FILE)) {
    try {
      const content = readFileSync(CACHE_FILE, 'utf-8');
      feedCache = JSON.parse(content);
      console.log(`[Cache] Loaded ${Object.keys(feedCache).length} cached feed entries.`);
    } catch (err) {
      console.warn('[Cache] Failed to load cache file:', err);
    }
  }
}

function saveCache() {
  try {
    writeFileSync(CACHE_FILE, JSON.stringify(feedCache, null, 2), 'utf-8');
    console.log(`[Cache] Saved ${Object.keys(feedCache).length} feed entries to cache.`);
  } catch (err) {
    console.warn('[Cache] Failed to save cache file:', err);
  }
}

// Date helper: check if date is within 7 days
function isPublishedWithin7Days(dateStr: string): boolean {
  if (!dateStr) return false;
  try {
    const publishedTime = new Date(dateStr).getTime();
    if (isNaN(publishedTime)) return false;
    const now = Date.now();
    const sevenDaysMs = 7 * 24 * 60 * 60 * 1000;
    // Handle potential future dates from timezone mismatches gently (allow up to 12h in the future)
    const diff = now - publishedTime;
    return diff >= -12 * 60 * 60 * 1000 && diff <= sevenDaysMs;
  } catch {
    return false;
  }
}

// Format date string to Beijing Time (UTC+8) YYYY-MM-DD HH:MM
function formatBeijingDate(dateStr: string): string {
  if (!dateStr) return '';
  try {
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return dateStr;
    const offset = 8 * 60 * 60 * 1000; // Beijing Time is UTC+8
    const beijingDate = new Date(date.getTime() + offset);
    const isoString = beijingDate.toISOString(); // e.g. 2026-06-23T01:28:18.000Z
    return isoString.substring(0, 16).replace('T', ' '); // 2026-06-23 01:28
  } catch {
    return dateStr;
  }
}

// Decode URL for clean display
function goUrlDecode(url: string): string {
  try {
    return decodeURIComponent(url);
  } catch {
    return url;
  }
}

function escapeMarkdownTitle(title: string): string {
  return title
    .replace(/\|/g, ' ')  // Replace pipe with space to match Go yaml-readme
    .replace(/\[/g, '\\[')   // Escape brackets
    .replace(/\]/g, '\\]')
    .replace(/\r?\n/g, ' ') // Remove newlines
    .trim();
}

// Fetch single feed with timeout and retry
async function fetchFeedWithTimeout(url: string): Promise<string> {
  for (let attempt = 1; attempt <= FETCH_RETRIES; attempt++) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
    try {
      const response = await fetch(url, {
        signal: controller.signal,
        headers: {
          'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
          'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml, */*'
        }
      });
      if (!response.ok) {
        throw new Error(`HTTP status ${response.status}`);
      }
      const text = await response.text();
      clearTimeout(timer);
      return text;
    } catch (err) {
      clearTimeout(timer);
      if (attempt === FETCH_RETRIES) {
        throw err;
      }
      // Wait 1s before retry
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
  throw new Error('Unexpected: retries exhausted');
}

// Parse feed XML text into FeedInfo
async function parseFeed(url: string, xmlText: string, fallbackLink: string): Promise<FeedInfo> {
  const rssParser = new Parser();
  const feed = await rssParser.parseString(xmlText);
  
  if (!feed.items || feed.items.length === 0) {
    throw new Error('No items in feed');
  }

  // Sort items descending by publication date safely (handling invalid dates)
  const sortedItems = [...feed.items].sort((a, b) => {
    const parseDate = (item: typeof a) => {
      const dateStr = item.isoDate || item.pubDate;
      if (!dateStr) return 0;
      const time = new Date(dateStr).getTime();
      return isNaN(time) ? 0 : time;
    };
    return parseDate(b) - parseDate(a);
  });

  const latest = sortedItems[0];
  const latestTitle = escapeMarkdownTitle(latest.title || 'Untitled');
  const latestLink = (latest.link || fallbackLink).replace(/\s+/g, '').trim();

  let publishedDate = '';
  const rawDate = latest.isoDate || latest.pubDate;
  if (rawDate) {
    try {
      const d = new Date(rawDate);
      if (!isNaN(d.getTime())) {
        publishedDate = d.toISOString().replace(/\.\d{3}/, '');
      } else {
        publishedDate = rawDate;
      }
    } catch {
      publishedDate = rawDate;
    }
  }

  return {
    latestTitle,
    latestLink,
    publishedDate,
    fetchedAt: Date.now()
  };
}

// Concurrency pool runner
async function runPool<T, R>(items: T[], fn: (item: T) => Promise<R>, limit: number): Promise<R[]> {
  const results: R[] = [];
  const promises: Promise<void>[] = [];
  let index = 0;

  async function worker() {
    while (index < items.length) {
      const curr = index++;
      results[curr] = await fn(items[curr]);
    }
  }

  for (let i = 0; i < Math.min(limit, items.length); i++) {
    promises.push(worker());
  }

  await Promise.all(promises);
  return results;
}

// Template AST Parser Definitions
type ASTNode =
  | { type: 'text'; content: string }
  | { type: 'eval'; content: string }
  | { type: 'if'; cond: string; body: ASTNode[] }
  | { type: 'range'; keyVar: string; valVar: string; body: ASTNode[] }
  | { type: 'range_item'; itemIndexVar: string | null; itemVar: string; itemsVar: string; body: ASTNode[] };

function tokenize(template: string): string[] {
  const rawTokens: { type: 'text' | 'tag'; content: string; trimLeft?: boolean; trimRight?: boolean }[] = [];
  let lastIndex = 0;
  const regex = /\{\{([\s\S]*?)\}\}/g;
  let match;
  while ((match = regex.exec(template)) !== null) {
    const text = template.substring(lastIndex, match.index);
    if (text) {
      rawTokens.push({ type: 'text', content: text });
    }

    const inner = match[1];
    const trimLeft = inner.startsWith('-');
    const trimRight = inner.endsWith('-');

    rawTokens.push({
      type: 'tag',
      content: `{{${inner}}}`,
      trimLeft,
      trimRight
    });
    lastIndex = regex.lastIndex;
  }
  const rest = template.substring(lastIndex);
  if (rest) {
    rawTokens.push({ type: 'text', content: rest });
  }

  // Apply whitespace trimming
  for (let i = 0; i < rawTokens.length; i++) {
    const tok = rawTokens[i];
    if (tok.type === 'tag') {
      if (tok.trimLeft) {
        // Strip trailing whitespace from previous text token
        const prev = rawTokens[i - 1];
        if (prev && prev.type === 'text') {
          prev.content = prev.content.trimEnd();
        }
      }
      if (tok.trimRight) {
        // Strip leading whitespace from next text token
        const next = rawTokens[i + 1];
        if (next && next.type === 'text') {
          next.content = next.content.trimStart();
        }
      }
    }
  }

  return rawTokens.map(t => t.content);
}

function parseTokens(tokens: string[]): ASTNode[] {
  let index = 0;

  function parse(): ASTNode[] {
    const nodes: ASTNode[] = [];
    while (index < tokens.length) {
      const token = tokens[index];
      if (token.startsWith('{{') && token.endsWith('}}')) {
        const inner = token.substring(2, token.length - 2).trim();
        // Strip leading/trailing Go template '-' indicators
        const cleaned = inner.replace(/^-|-$/g, '').trim();

        if (cleaned.startsWith('range ')) {
          index++;
          const rangeContent = cleaned.substring(6).trim();
          if (rangeContent.includes(',')) {
            const parts = rangeContent.split(':=');
            const vars = parts[0].split(',').map(v => v.trim());
            const expr = parts[1].trim();
            const body = parse();

            if (vars[0] === '$key') {
              nodes.push({
                type: 'range',
                keyVar: vars[0],
                valVar: vars[1],
                body
              });
            } else {
              nodes.push({
                type: 'range_item',
                itemIndexVar: vars[0],
                itemVar: vars[1],
                itemsVar: expr,
                body
              });
            }
          } else {
            const parts = rangeContent.split(':=');
            const itemVar = parts[0].trim();
            const expr = parts[1].trim();
            const body = parse();
            nodes.push({
              type: 'range_item',
              itemIndexVar: null,
              itemVar,
              itemsVar: expr,
              body
            });
          }
        } else if (cleaned.startsWith('if ')) {
          index++;
          const cond = cleaned.substring(3).trim();
          const body = parse();
          nodes.push({
            type: 'if',
            cond,
            body
          });
        } else if (cleaned === 'end') {
          index++;
          return nodes;
        } else {
          nodes.push({ type: 'eval', content: cleaned });
          index++;
        }
      } else {
        nodes.push({ type: 'text', content: token });
        index++;
      }
    }
    return nodes;
  }

  return parse();
}

// Template Evaluation Helper Context
interface EvalContext {
  groups: Group[];
  rootData: Record<string, YamlItem[]>;
  totalItemsCount: number;
  vars: Record<string, any>;
  dot: any;
  isJson: boolean;
  isStructured: boolean;
  resolvedFeeds: Record<string, FeedInfo | null>;
}

// Parse args supporting nested parentheses and quoted string literals
function parseArgs(str: string): string[] {
  const args: string[] = [];
  let depth = 0;
  let inQuote = false;
  let current = '';
  for (let i = 0; i < str.length; i++) {
    const char = str[i];
    if (char === '"' && (i === 0 || str[i - 1] !== '\\')) {
      inQuote = !inQuote;
      current += char;
    } else if (char === '(' && !inQuote) {
      depth++;
      current += char;
    } else if (char === ')' && !inQuote) {
      depth--;
      current += char;
    } else if (char === ' ' && depth === 0 && !inQuote) {
      if (current.trim()) {
        args.push(current.trim());
      }
      current = '';
    } else {
      current += char;
    }
  }
  if (current.trim()) {
    args.push(current.trim());
  }
  return args.map(arg => {
    if (arg.startsWith('(') && arg.endsWith(')')) {
      return arg.substring(1, arg.length - 1).trim();
    }
    return arg;
  });
}

function evaluateExpr(expr: string, ctx: EvalContext): any {
  expr = expr.trim();

  // Root len helper functions
  if (expr === 'lenGroupNum') return ctx.groups.length;
  if (expr === 'lenItemNum') return ctx.totalItemsCount;

  if (expr.startsWith('len ')) {
    const arg = expr.substring(4).trim();
    const val = evaluateExpr(arg, ctx);
    if (val && typeof val === 'object') {
      if (Array.isArray(val)) return val.length;
      return Object.keys(val).length;
    }
    return 0;
  }

  if (expr.startsWith('goUrlDecode ')) {
    const arg = expr.substring(12).trim();
    const val = evaluateExpr(arg, ctx);
    return goUrlDecode(val || '');
  }

  if (expr.startsWith('getFeedLatestPostPublishedDate ')) {
    const arg = expr.substring(31).trim();
    const feedUrl = evaluateExpr(arg, ctx);
    if (!feedUrl) return '';
    const feed = ctx.resolvedFeeds[feedUrl];
    if (!feed) return '';
    const dateStr = feed.publishedDate.replace(/\.\d{3}/, '');
    return ctx.isStructured ? dateStr : formatBeijingDate(dateStr);
  }

  if (expr.startsWith('getFeedLatestPost ')) {
    const rest = expr.substring(18).trim();
    const parts = parseArgs(rest);
    const feedUrl = evaluateExpr(parts[0], ctx);
    const fallbackLink = evaluateExpr(parts[1], ctx);

    if (!feedUrl) return `[${fallbackLink}](${fallbackLink})`;
    const feed = ctx.resolvedFeeds[feedUrl];
    if (feed && feed.latestTitle) {
      const isNew = isPublishedWithin7Days(feed.publishedDate);
      let md = `[${feed.latestTitle}](${feed.latestLink})`;
      if (isNew) {
        md += `![news](https://github.com/ChanceYu/front-end-rss/blob/master/assets/new.png?raw=true)`;
      }
      return md;
    } else {
      return `[${fallbackLink}](${fallbackLink})`;
    }
  }

  // Variable Assignments & Operations
  const assignMatch = expr.match(/^(\$[a-zA-Z0-9_]+)\s*(:=|=)\s*(.*)$/);
  if (assignMatch) {
    const [_, varName, op, valExpr] = assignMatch;
    const val = evaluateExpr(valExpr, ctx);
    
    if (op === ':=') {
      ctx.vars[varName] = val;
    } else {
      // Reassignment: walk up prototype chain
      let scope = ctx.vars;
      let found = false;
      while (scope) {
        if (Object.prototype.hasOwnProperty.call(scope, varName)) {
          scope[varName] = val;
          found = true;
          break;
        }
        scope = Object.getPrototypeOf(scope);
      }
      if (!found) {
        ctx.vars[varName] = val;
      }
    }
    return '';
  }

  if (expr.startsWith('add ')) {
    const parts = expr.substring(4).trim().split(/\s+/);
    const a = evaluateExpr(parts[0], ctx);
    const b = evaluateExpr(parts[1], ctx);
    return Number(a) + Number(b);
  }

  if (expr.startsWith('sub ')) {
    const parts = expr.substring(4).trim().split(/\s+/);
    const a = evaluateExpr(parts[0], ctx);
    const b = evaluateExpr(parts[1], ctx);
    return Number(a) - Number(b);
  }

  if (expr.startsWith('lt ')) {
    const rest = expr.substring(3).trim();
    const parts = parseArgs(rest);
    const a = evaluateExpr(parts[0], ctx);
    const b = evaluateExpr(parts[1], ctx);
    return a < b;
  }

  // Variable paths
  if (expr === '.') return ctx.dot;
  if (expr.startsWith('$')) {
    const parts = expr.split('.');
    const varName = parts[0];
    let val = ctx.vars[varName];
    for (let i = 1; i < parts.length; i++) {
      if (val && typeof val === 'object') {
        val = val[parts[i]];
      } else {
        val = undefined;
      }
    }
    return val;
  }

  // Literals
  if (expr.startsWith('"') && expr.endsWith('"')) {
    return expr.substring(1, expr.length - 1);
  }
  if (!isNaN(Number(expr))) {
    return Number(expr);
  }

  return '';
}

function renderAST(nodes: ASTNode[], ctx: EvalContext): string {
  let out = '';
  for (const node of nodes) {
    if (node.type === 'text') {
      out += node.content;
    } else if (node.type === 'eval') {
      const val = evaluateExpr(node.content, ctx);
      let valStr = val !== undefined ? String(val) : '';
      if (ctx.isJson) {
        // Use JSON.stringify to safely escape all JSON special characters
        valStr = JSON.stringify(valStr).slice(1, -1);
      }
      out += valStr;
    } else if (node.type === 'if') {
      const condVal = evaluateExpr(node.cond, ctx);
      if (condVal) {
        out += renderAST(node.body, ctx);
      }
    } else if (node.type === 'range') {
      const dotVal = evaluateExpr('.', ctx);
      const entries = Object.entries(dotVal);
      for (const [k, v] of entries) {
        const prevVars = ctx.vars;
        const prevDot = ctx.dot;

        // Create lexical prototype scope
        ctx.vars = Object.create(prevVars);
        ctx.vars[node.keyVar] = k;
        ctx.vars[node.valVar] = v;
        ctx.dot = v;

        out += renderAST(node.body, ctx);

        ctx.vars = prevVars;
        ctx.dot = prevDot;
      }
    } else if (node.type === 'range_item') {
      const items = evaluateExpr(node.itemsVar, ctx);
      if (Array.isArray(items)) {
        for (let idx = 0; idx < items.length; idx++) {
          const item = items[idx];
          const prevVars = ctx.vars;
          const prevDot = ctx.dot;

          // Create lexical prototype scope
          ctx.vars = Object.create(prevVars);
          if (node.itemIndexVar) {
            ctx.vars[node.itemIndexVar] = idx;
          }
          ctx.vars[node.itemVar] = item;
          ctx.dot = item;

          out += renderAST(node.body, ctx);

          ctx.vars = prevVars;
          ctx.dot = prevDot;
        }
      }
    }
  }
  return out;
}

// Main Execution
async function main() {
  console.log('🚀 Starting Bun README Generator...');
  const startTime = Date.now();

  // Load feed cache
  loadCache();

  // 1. Scan and parse all YAML files in items/*/*.yaml
  const glob = new Glob('items/*/*.yaml');
  const yamlFiles = Array.from(glob.scanSync('.')).sort();
  console.log(`[Files] Found ${yamlFiles.length} item files.`);

  const items: YamlItem[] = [];
  const groupsOrder: string[] = [];
  const groupsMap: Record<string, YamlItem[]> = {};

  for (const file of yamlFiles) {
    try {
      const content = readFileSync(file, 'utf-8');
      const parsed = YAML.parse(content) as any;
      if (!parsed || !parsed.kind) {
        console.warn(`[Files] Invalid YAML format in ${file}, skipping.`);
        continue;
      }
      const item: YamlItem = {
        kind: parsed.kind,
        owner: parsed.owner || '',
        name: parsed.name || '',
        link: parsed.link || '',
        desc: parsed.desc || '',
        desc_en: parsed.desc_en,
        feed_url: parsed.feed_url || '',
        filePath: file
      };
      items.push(item);

      // Track group structure matching glob order
      if (!groupsMap[item.kind]) {
        groupsMap[item.kind] = [];
        groupsOrder.push(item.kind);
      }
      groupsMap[item.kind].push(item);
    } catch (err) {
      console.error(`[Files] Error parsing ${file}:`, err);
    }
  }

  // Construct the final sorted groups list
  const groups: Group[] = groupsOrder.map(key => ({
    key,
    val: groupsMap[key]
  }));

  // Construct rootData for '.' context in templates
  const rootData: Record<string, YamlItem[]> = {};
  for (const g of groups) {
    rootData[g.key] = g.val;
  }

  console.log(`[Groups] Grouped into ${groups.length} categories.`);

  // 2. Fetch and parse feeds in parallel
  const uniqueFeedUrls = Array.from(new Set(items.map(item => item.feed_url).filter(Boolean)));
  console.log(`[Feeds] Found ${uniqueFeedUrls.length} unique feed URLs. Fetching...`);

  const resolvedFeeds: Record<string, FeedInfo | null> = {};

  await runPool(
    uniqueFeedUrls,
    async (url) => {
      // Find fallback link from any item using this feed url
      const sampleItem = items.find(item => item.feed_url === url);
      const fallbackLink = (sampleItem ? sampleItem.link : url).trim();

      // Check Cache first
      if (!forceFetch) {
        const cached = feedCache[url];
        if (cached && Date.now() - cached.fetchedAt < CACHE_DURATION_MS) {
          resolvedFeeds[url] = cached;
          console.log(`[Feeds] [CACHE HIT] ${url}`);
          return;
        }
      }

      // Fetch fresh
      console.log(`[Feeds] [FETCHING] ${url}`);
      try {
        const xmlText = await fetchFeedWithTimeout(url);
        const parsedInfo = await parseFeed(url, xmlText, fallbackLink);
        resolvedFeeds[url] = parsedInfo;
        feedCache[url] = parsedInfo; // Save back to cache
        console.log(`[Feeds] [SUCCESS] ${url} -> ${parsedInfo.latestTitle} (${parsedInfo.publishedDate})`);
      } catch (err: any) {
        console.warn(`[Feeds] [FAILED] ${url}: ${err.message || err}. Falling back to default.`);
        resolvedFeeds[url] = null;
      }
    },
    CONCURRENCY_LIMIT
  );

  // Save feed cache
  saveCache();

  // 3. Render and save job templates
  for (const job of DEFAULT_JOBS) {
    if (!existsSync(job.template)) {
      console.warn(`[Templates] Template not found: ${job.template}, skipping job.`);
      continue;
    }

    console.log(`[Templates] Rendering ${job.template} -> ${job.output}`);
    try {
      const templateContent = readFileSync(job.template, 'utf-8');
      const tokens = tokenize(templateContent);
      const ast = parseTokens(tokens);

      const isJson = job.output.endsWith('.json');
      const isStructured = isJson || job.output.endsWith('.yaml');
      const ctx: EvalContext = {
        groups,
        rootData,
        totalItemsCount: items.length,
        vars: {},
        dot: rootData,
        isJson,
        isStructured,
        resolvedFeeds
      };

      const rendered = renderAST(ast, ctx);
      
      // Ensure target directory exists
      mkdirSync(dirname(job.output), { recursive: true });
      writeFileSync(job.output, rendered, 'utf-8');
      console.log(`[Templates] Saved to ${job.output}`);
    } catch (err) {
      console.error(`[Templates] Error rendering ${job.template}:`, err);
    }
  }

  const durationSec = ((Date.now() - startTime) / 1000).toFixed(2);
  console.log(`\n🎉 README generation completed successfully in ${durationSec}s.`);
}

main().catch(err => {
  console.error('Fatal error during README generation:', err);
  process.exit(1);
});
