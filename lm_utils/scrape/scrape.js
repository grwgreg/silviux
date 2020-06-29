//This file gets text from wikipedia pages and walks links, doing some simple tests to try to build programming related corpus
//https://www.twilio.com/blog/web-scraping-and-parsing-html-with-node-js-and-cheerio
const fs = require('fs');
const cheerio = require('cheerio');
const got = require('got');

//let wiki = 'https://en.wikipedia.org/wiki/Computer_programming'
//let wiki = 'https://en.wikipedia.org/wiki/Big_O_notation'
let wiki = 'https://en.wikipedia.org/wiki/Software_engineering'
let wikiRoot = 'https://en.wikipedia.org'
let wikiPrefix = '/wiki'

const visited = new Set()

async function scrape(url, level) {
	if (level > 3) return;
	if (visited.has(url)) return;
	visited.add(url);
  let response;
  try {
		console.log('fetching ', url)
		await new Promise(res => setTimeout(res, 100));
		response = await got(url);
  } catch(e) {
		console.log(e);
    return;
  }
  const $ = cheerio.load(response.body);

  //too many names, isbn junk in wiki references
	$('.references').remove();
	$('.reflist').remove();
  //these expandable boxes at bottom contain too many unrelated links
	$('.navbox').remove();
  //pre is code, math tags show up as junk in text() call
	$('pre').remove();
	$('math').remove();

  //imgs full of specific names of people and companies
	$('.thumb').remove();

  //anything within noscript gets added to text() for some reason, is including img html in texts
	$('noscript').remove();

	const text = $('#mw-content-text').text();
  
  //manually checking for programming related terms before adding will allow deeper search without adding unrelated links
  let hits = 0;
  if (text.toLowerCase().indexOf('computer') > -1) hits++;
  if (text.toLowerCase().indexOf('software') > -1) hits++;
  if (text.toLowerCase().indexOf('programming') > -1) hits++;
  if (hits == 0) { console.log('skipping:', url); return;}

	let urls = [];
  $('#mw-content-text a').each((i, el) => {
		let href = el.attribs.href;
		if (!href) return;
		if (href.indexOf(wikiPrefix) !== 0) return;

    //wikipedia specific link names to skip
    if (href.indexOf('File:') !== -1) return;
    if (href.indexOf('Help:') !== -1) return;
    if (href.indexOf('Wikipedia:') !== -1) return;
    if (href.indexOf('Talk:') !== -1) return;
    if (href.indexOf('Special:') !== -1) return;
    if (href.indexOf('Template:') !== -1) return;
    if (href.indexOf('Template_talk:') !== -1) return;
    if (href.indexOf('Category:') !== -1) return;

    //these terms add too much unrelated junk "history of computing" "philosophy of", schools, literal languages
    if (href.toLowerCase().indexOf('philosophy') !== -1) return;
    if (href.toLowerCase().indexOf('history') !== -1) return;
    if (href.toLowerCase().indexOf('city') !== -1) return;
    if (href.toLowerCase().indexOf('university') !== -1) return;
    if (href.toLowerCase().indexOf('school') !== -1) return;
		urls.push(wikiRoot + href);
	});

	const id = guid();

	fs.appendFile('urls', id+":::::::::::"+url+"\n", err => {if(err) {throw err}});
	fs.writeFile('text/'+id, text, err => {if(err) {throw err}});

	for (let i = 0; i < urls.length; i++) {
		//wait a bit to be nice
		await scrape(urls[i],level+1);
	}
  return true

}

//https://stackoverflow.com/questions/6860853/generate-random-string-for-div-id
function guid() {
    var S4 = function() {
       return (((1+Math.random())*0x10000)|0).toString(16).substring(1);
    };
    return (S4()+S4()+"-"+S4()+"-"+S4()+"-"+S4());
}

async function main() {
  try {
		await scrape(wiki, 1);
    console.log('............')
    console.log('done')
  } catch(e) {
		console.log(e);
  }
}

main();
