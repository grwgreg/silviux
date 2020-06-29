//This file gets text from mdn docs and walks links
//Note the method of waiting between requests in this file still makes some concurrent requests
//see scrape.js for the better implemenation
//https://www.twilio.com/blog/web-scraping-and-parsing-html-with-node-js-and-cheerio
const fs = require('fs');
const cheerio = require('cheerio');
const got = require('got');

//const mdn= 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference';
let mdn= 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object';
let mdnRoot = 'https://developer.mozilla.org'
let mdnPrefix = '/en-US/docs/Web/JavaScript' 

const visited = new Set()

async function scrape(url, level) {
	if (level > 5) return;
	if (visited.has(url)) return;
	visited.add(url);
  let response;
  try {
		response = await got(url);
		console.log(url)
  } catch(e) {
		console.log(e);
    return;
  }
  const $ = cheerio.load(response.body);

	//remove long lists of usernames
	$('.contributors').text('');
	//remove browser compatibility, TODO make sure firefox,safari etc make way into lexicon somehow
	$('.bc-data').text('');
//note, cheerio libs uses jquery map style, it rewraps your mapped objs in a jquery obj so its weird
	let urls = [];
  $('a').each((i, el) => {
		let href = el.attribs.href;
		if (!href) return;
		if (href.includes('compare?to=') || href.includes('$revision')) return;
		if (href.indexOf(mdnPrefix) !== 0) return;
		urls.push(mdnRoot + href);
	});

	const text = $('.article').text();
	const id = guid();

	fs.appendFile('urls', id+":::::::::::"+url+"\n", err => {if(err) {throw err}});
	fs.writeFile('text/'+id, text, err => {if(err) {throw err}});

	for (let i = 0; i < urls.length; i++) {
		//TODO 
    //Change to match the wikipedia scrape.js file, ie this await/pause doesn't work quite right
    //it still makes concurrent calls, should instead await scrape(..) and sleep in body of scrape fn
		await new Promise(res => setTimeout(res, 500));
		scrape(urls[i],level+1);
	}

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
		scrape(mdn, 1);
  } catch(e) {
		console.log(e);
  }
}

main();
