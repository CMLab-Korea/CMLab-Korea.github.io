const assert = require('node:assert/strict');
const {test} = require('node:test');
require('../assets/js/journal-metrics.js');
const {match, summarize} = globalThis.CMLabJournalMetrics;
const {readFileSync} = require('node:fs');
const {join} = require('node:path');
const directory = process.argv[2] || join(__dirname, '../data');
const registry = JSON.parse(readFileSync(join(directory, 'journals.json'), 'utf8'));
const papers = JSON.parse(readFileSync(join(directory, 'publications.json'), 'utf8'));

test('current public catalog and registry reconcile without fixed counts', () => {
  const ids = papers.map(paper => paper.id);
  assert.equal(new Set(ids).size, ids.length);
  const journalPapers = papers.filter(paper => paper.type === 'Journal');
  const published = journalPapers.filter(paper => paper.status === 'Published');
  const report = summarize(papers, registry);
  const expected = new Map();
  for (const paper of journalPapers) {
    const mapping = match(paper, registry.journals);
    assert.equal(mapping.status, 'matched', paper.catalog_number);
    if (paper.status === 'Published') {
      const key = mapping.journal.journal_id;
      expected.set(key, (expected.get(key) || 0) + 1);
    }
  }
  assert.equal(report.counts.total, published.length);
  assert.deepEqual(report.rows.map(row => row.papers), report.rows.map(row => expected.get(row.journal.journal_id) || 0));
  assert.equal(report.counts.covered, report.metricsByPaper.size);
  assert.ok(report.counts.covered <= report.counts.total);
  assert.ok(report.counts.top1 <= report.counts.top5 && report.counts.top5 <= report.counts.top10);
  assert.ok([...report.metricsByPaper.keys()].every(id => published.some(paper => paper.id === id)));
});
