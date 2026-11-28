const assert = require('node:assert/strict');
const {test} = require('node:test');
require('../assets/js/journal-metrics.js');
const {match, select, summarize} = globalThis.CMLabJournalMetrics;
const publicRegistry = require('../data/journals.json');
const papers = require('../data/publications.json');
const fixture = require('./fixtures/jcr-synthetic.json');
const synthetic = {
  journal_id:'synthetic-journal', official_name:'Synthetic Journal', aliases:['Synth'],
  issn:'0162-8828', metrics:fixture.records
};
const edition = publicRegistry.public_edition;

test('public catalog counts, exact existing journal matches and blank approved metrics', () => {
  assert.deepEqual(Object.fromEntries(['Conference','Journal','Preprint'].map(type => [
    type, papers.filter(p => p.type === type).length
  ])), {Conference:20, Journal:8, Preprint:15});
  const report = summarize(papers, publicRegistry);
  assert.deepEqual(report.rows.map(r => r.papers), [2,2,3,1]);
  assert.equal(report.review.length, 0);
  assert.equal(report.counts.covered, 0);
  assert.ok(publicRegistry.journals.every(j => !j.metrics.length));
});

test('matching priority, unknown, ambiguous and skipped types', () => {
  const list = [synthetic, {...synthetic, journal_id:'other', issn:null}];
  assert.equal(match({type:'Journal',journal_id:'other',issn:synthetic.issn},list).journal.journal_id,'other');
  assert.equal(match({type:'Journal',issn:synthetic.issn},list).journal.journal_id,'synthetic-journal');
  assert.equal(match({type:'Journal',venue:'Synthetic Journal'},[synthetic]).status,'matched');
  assert.equal(match({type:'Journal',venue_short:"Synth'26"},[synthetic]).status,'matched');
  assert.equal(match({type:'Journal',venue_short:"Synth'26"},list).status,'ambiguous');
  assert.equal(match({type:'Journal',journal_id:'unknown',venue:'Synthetic Journal'}, list).status,'unmatched');
  for (const type of ['Conference','Preprint','Under Review']) {
    assert.equal(match({type,venue:'Synthetic Journal'},list).status,'excluded');
  }
});

test('edition modes, revisions and distinct calculations', () => {
  const revision = {...fixture.records[1],revision:2,revision_date:'2026-06-24',last_verified:'2026-06-25',jif:9};
  const journal = {...synthetic,metrics:[...synthetic.metrics,revision]};
  assert.equal(select(journal,edition).record.jif,9);
  assert.equal(select(journal,edition,{mode:'historical',year:2024}).record.jif,7);
  assert.equal(select(journal,edition,{mode:'publication',publicationYear:2024}).record.jif,7);
  assert.equal(select(journal,edition,{mode:'asOf',asOf:'2026-06-21'}).record.jif,8);
  assert.equal(select(journal,edition,{mode:'asOf',asOf:'2026-05-01'}).record.jif,7);
  const metric = select(journal,edition);
  assert.equal(metric.category.name,'Synthetic Vision Category');
  assert.deepEqual(metric.percentages,{s2:5,officialTop:4,rankBased:3});
});

test('no fallback when the edition is missing, incomplete, unapproved or unverified', () => {
  for (const metrics of [[fixture.records[0]],
    [fixture.records[0], {...fixture.records[1],category_completeness:'partial'}],
    [fixture.records[0], {...fixture.records[1],public_authorized:false}],
    [fixture.records[0], {...fixture.records[1],verification_status:'unverified'}]]) {
    assert.equal(select({...synthetic,metrics},edition),null);
  }
});

test('published paper totals are deduplicated and top tiers are cumulative', () => {
  const paper = {id:5,type:'Journal',status:'Published',venue:'Synthetic Journal'};
  const report = summarize([paper,paper,{...paper,id:6,venue:'Unknown'},
    {...paper,id:7,status:'Accepted'}],{journals:[synthetic],public_edition:edition});
  assert.deepEqual(report.counts,{q1:1,top10:1,top5:1,top1:0,covered:1,total:2,scieVerified:0,scieReviewed:0});
  assert.equal(report.review.length,1);
});

test('optional rank fields and separate SCIE evidence', () => {
  const record = {...fixture.records[1],categories:fixture.records[1].categories.map(c =>
    ({...c,rank:null,total:null,jif_percentile:null,rank_percent:null}))};
  const journal = {...synthetic,metrics:[record],scie:[
    {year:2025,status:'indexed',verification_status:'verified',public_authorized:true},
    {year:2026,status:'indexed',verification_status:'verified',public_authorized:false}
  ]};
  assert.deepEqual(select(journal,edition).percentages,{s2:5,officialTop:null,rankBased:null});
  const make = year => ({id:year,year,type:'Journal',status:'Published',venue:'Synthetic Journal'});
  const report = summarize([make(2025),make(2026)],{journals:[journal],public_edition:edition});
  assert.equal(report.counts.total,2);
  assert.equal(report.counts.covered,2);
  assert.equal(report.counts.scieVerified,1);
  assert.equal(report.counts.scieReviewed,1);
});
