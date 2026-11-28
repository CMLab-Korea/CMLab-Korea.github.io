/* Public data only. These selectors also support downstream report consumers. */
(() => {
  'use strict';
  const normalize = value => String(value ?? '').normalize('NFKC').toLowerCase()
    .trim().replace(/[^\p{L}\p{N}]+/gu, ' ').trim();
  const compare = (a, b) => {
    const left = Array.from(a, char => char.codePointAt(0));
    const right = Array.from(b, char => char.codePointAt(0));
    for (let index = 0; index < Math.min(left.length, right.length); index++) {
      if (left[index] !== right[index]) return left[index] - right[index];
    }
    return left.length - right.length;
  };
  const serial = value => String(value ?? '').trim().toUpperCase().replace(/-/g, '');

  function match(paper, journals) {
    if (paper.type !== 'Journal') return {status: 'excluded'};
    const values = [normalize(paper.venue), normalize(paper.venue_short?.replace(/['’]\d{2,4}$/, ''))].filter(Boolean);
    const ids = [serial(paper.issn), serial(paper.eissn)].filter(Boolean);
    const find = predicate => journals.filter(predicate);
    let candidates;
    if (paper.journal_id) {
      candidates = find(j => j.journal_id === paper.journal_id);
    } else if (ids.length) {
      candidates = find(j => [serial(j.issn), serial(j.eissn)].some(id => ids.includes(id)));
    } else {
      const official = find(j => values.includes(normalize(j.official_name)));
      candidates = official.length ? official : find(j => j.aliases.some(name => values.includes(normalize(name))));
    }
    if (candidates.length === 1) return {status: 'matched', journal: candidates[0]};
    return {status: candidates.length ? 'ambiguous' : 'unmatched'};
  }

  function publicRecord(record) {
    return record.public_authorized === true && record.verification_status === 'verified'
      && record.source === 'S2Journal' && record.ranking === 'jcr';
  }

  function select(journal, edition, options = {}) {
    const {mode = 'common', year, publicationYear, asOf} = options;
    if (!['common', 'historical', 'publication', 'asOf'].includes(mode)) return null;
    const rows = journal.metrics.filter(publicRecord);
    const eligible = rows.filter(record => {
      if (mode === 'asOf') return asOf && (record.revision === 1 ? record.release_date : record.revision_date)
        && (record.revision === 1 ? record.release_date : record.revision_date) <= asOf;
      const dataYear = mode === 'historical' ? year : mode === 'publication' ? publicationYear : edition.data_year;
      return record.data_year === dataYear && (mode !== 'common' || record.release_year === edition.release_year);
    }).sort((a, b) => b.data_year - a.data_year || b.revision - a.revision);
    const record = eligible[0];
    const positiveIntOrNull = value => value === null || (Number.isInteger(value) && value > 0);
    if (!record || record.category_completeness !== 'complete' || record.category_count !== record.categories.length
        || !record.categories.length || !record.categories.every(c => Number.isFinite(c.s2_if_percent)
          && c.s2_if_percent >= 0 && c.s2_if_percent <= 100
          && positiveIntOrNull(c.rank) && positiveIntOrNull(c.total)
          && (c.rank === null || c.total === null || c.rank <= c.total) && /^Q[1-4]$/.test(c.quartile))
        || record.categories.some(c => !normalize(c.name))
        || new Set(record.categories.map(c => normalize(c.name))).size !== record.categories.length
        || !Number.isFinite(record.jif) || record.jif < 0) return null;
    const category = [...record.categories].sort((a, b) => a.s2_if_percent - b.s2_if_percent
      || compare(normalize(a.name), normalize(b.name)) || compare(a.name, b.name))[0];
    return {record, category, percentages: {
      s2: category.s2_if_percent,
      officialTop: Number.isFinite(category.jif_percentile) ? 100 - category.jif_percentile : null,
      rankBased: category.rank === null || category.total === null ? null : 100 * category.rank / category.total
    }};
  }

  function isPublishedJournal(paper) {
    return paper.type === 'Journal' && paper.status === 'Published';
  }

  function scieStatus(paper, journal) {
    const evidence = journal.scie?.find(entry => entry.year === paper.year
      && entry.verification_status === 'verified' && entry.public_authorized === true);
    return ['indexed', 'not_indexed'].includes(evidence?.status) ? evidence.status : 'unconfirmed';
  }

  function summarize(items, registry) {
    const published = items.filter(isPublishedJournal);
    const distinct = [...new Map(published.map(paper => [paper.id, paper])).values()];
    const rows = registry.journals.map(journal => ({journal, papers: 0, metric: select(journal, registry.public_edition)}));
    const byJournal = new Map(rows.map(row => [row.journal.journal_id, row]));
    const review = [];
    const metricsByPaper = new Map();
    const counts = {q1: 0, top10: 0, top5: 0, top1: 0, covered: 0, total: distinct.length, scieVerified: 0, scieReviewed: 0};
    for (const paper of distinct) {
      const result = match(paper, registry.journals);
      if (result.status !== 'matched') {
        review.push({paper, status: result.status});
        continue;
      }
      const row = byJournal.get(result.journal.journal_id);
      row.papers++;
      const scie = scieStatus(paper, result.journal);
      if (scie !== 'unconfirmed') counts.scieReviewed++;
      if (scie === 'indexed') counts.scieVerified++;
      if (!row.metric) continue;
      metricsByPaper.set(paper.id, row.metric);
      const category = row.metric.category;
      counts.covered++;
      if (category.quartile === 'Q1') counts.q1++;
      for (const top of [10, 5, 1]) if (category.s2_if_percent <= top) counts['top' + top]++;
    }
    const allJournalPapersScie = counts.total > 0 && counts.scieVerified === counts.total
      && counts.total === items.filter(p => p.type === 'Journal').length;
    return {rows, counts, metricsByPaper, review, allJournalPapersScie};
  }

  globalThis.CMLabJournalMetrics = {match, select, summarize};
})();
