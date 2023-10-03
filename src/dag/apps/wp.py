import re, urllib

import dag


@dag.cmd
def wpedit(url):
	content = dag.get.HTML(url)
	body = content.body[0]

	try:
		pageid = re.match(r".*page-id-(\d+).*", body.cls).group(1)
	except IndexError:
		return "No WP page-id class identified in <body> tag"


	urlparts = urllib.parse.urlparse(url, scheme='', allow_fragments=True)

	return f"{urlparts.scheme}://{urlparts.netloc}/wp-admin/post.php?post={pageid}&action=edit"