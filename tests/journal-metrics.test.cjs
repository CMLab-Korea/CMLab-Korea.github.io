const assert = require('node:assert/strict');
const {test} = require('node:test');
require('../assets/js/journal-metrics.js');
const {match, select, summarize} = globalThis.CMLabJournalMetrics;
const fixture = require('./fixtures/jcr-synthetic.json');
const synthetic = {...fixture.registry.journals[0], metrics:fixture.records};
const edition = fixture.registry.public_edition;

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
  assert.deepEqual([...report.metricsByPaper.keys()], [5]);
  assert.equal(report.allJournalPapersScie, false);
});

test('optional rank fields and separate SCIE evidence', () => {
  const record = {...fixture.records[1],categories:fixture.records[1].categories.map(c =>
    ({...c,rank:null,total:null,jif_percentile:null,rank_percent:null}))};
  const journal = {...synthetic,metrics:[record],scie:[
    {year:2025,status:'indexed',verification_status:'verified',public_authorized:true},
    {year:2026,status:'indexed',verification_status:'verified',public_authorized:false},
    {year:2024,status:'not_indexed',verification_status:'verified',public_authorized:true}
  ]};
  assert.deepEqual(select(journal,edition).percentages,{s2:5,officialTop:null,rankBased:null});
  const make = year => ({id:year,year,type:'Journal',status:'Published',venue:'Synthetic Journal'});
  const registry = {journals:[journal],public_edition:edition};
  const report = summarize([make(2025),make(2026),make(2024)],registry);
  assert.equal(report.counts.total,3);
  assert.equal(report.counts.covered,3);
  assert.equal(report.counts.scieVerified,1);
  assert.equal(report.counts.scieReviewed,2);
  assert.equal(report.allJournalPapersScie,false);
  assert.equal(summarize([make(2025)],registry).allJournalPapersScie,true);
});

test('zero, partial and full coverage after adding a journal and publication', () => {
  const items = [...fixture.publications,
    {id:5,catalog_number:'J3',type:'Journal',status:'Published',year:2026,venue:'Synthetic New Journal'}];
  const added = {...synthetic,journal_id:'synthetic-new',official_name:'Synthetic New Journal',aliases:[],issn:null,metrics:[]};
  const summarizeWith = journals => summarize(items,{journals,public_edition:edition});
  assert.equal(summarizeWith([...fixture.registry.journals,added]).counts.covered,0);
  assert.equal(summarizeWith([synthetic,added]).counts.covered,1);
  const full = summarizeWith([synthetic,{...added,metrics:fixture.records}]);
  assert.equal(full.counts.total,2);
  assert.equal(full.counts.covered,2);
  assert.deepEqual([...full.metricsByPaper.keys()],[1,5]);
});

test('common edition change and revision preserve historical selection', () => {
  const added = {...fixture.records[1],data_year:2026,release_year:2027,release_date:'2027-06-20',last_verified:'2027-06-21'};
  const revision = {...added,revision:2,revision_date:'2027-07-01',last_verified:'2027-07-02'};
  const journal = {...synthetic,metrics:[...fixture.records,added,revision]};
  assert.equal(select(journal,edition).record.data_year,2025);
  assert.equal(select(journal,{data_year:2026,release_year:2027}).record.revision,2);
  assert.equal(select(journal,edition,{mode:'historical',year:2024}).record.data_year,2024);
});
