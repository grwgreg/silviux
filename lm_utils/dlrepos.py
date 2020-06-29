import urllib.request, urllib.error, urllib.parse
import json
import os

#download top github repos by stars
#api is paginated 30 repos at a time, use page=2 to get more

contents = urllib.request.urlopen("https://api.github.com/search/repositories?q=language:javascript&sort=stars&order=desc").read()
data = json.loads(contents)
# print(data)
# data = map(lambda x: x['git_url'], data['items'][:5])
data = [x['git_url'] for x in data['items'][:30]]#should only be 30 anyway
print(json.dumps(data, sort_keys=True, indent=4, separators=(',', ': ')))

os.chdir('repos')
for url in data:
    os.system("git clone --depth=1 %s" % (url,))
