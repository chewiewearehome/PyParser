import urllib.request as urllib2
from bs4 import BeautifulSoup
import transliterate
import re
import os
import codecs


def main(category_href): # Parse chosen category
	html_doc = urllib2.urlopen(category_href)
	soup = BeautifulSoup(html_doc, "html.parser")

	array_hrefs = []

	for link in soup.find_all('a'):
		href = link.get('href')

		if href.startswith(category_href):
			array_hrefs.append(href)

	array_hrefs = list(set(array_hrefs)) # avoiding same links

	# global variables and counters

	global img_global_counter
	img_global_counter = 792 

	global post_global_counter
	post_global_counter = 970

	global sql_global
	sql_global = codecs.open("sql_global.sql","a+", "utf-8")

	for html_doc_inside_href in array_hrefs:
		post_global_counter += 1
		img_global_counter += parse_inside_page(html_doc_inside_href, img_global_counter)
		
	sql_global.close()


def parse_inside_page(html_doc_inside_href, img_global_counter): # Parse particular page
	html_doc_inside = urllib2.urlopen(html_doc_inside_href)
	soup_inside = BeautifulSoup(html_doc_inside, "html.parser")

	title = soup_inside.select_one('.Titulo').get_text() # class can be changed to those which contain Main Heading/title of the page
	title_translaterate = translaterate(title)

	content_text = try_except('.objectosSubBlock', soup_inside) + "\n" + try_except('.text_body', soup_inside) # classes can be changed to those which contain text content

	img_counter = 0
	img_array = []

	content_div = soup_inside.select_one('.Content')
	
	for link in content_div.find_all('img'):
		href = u"{}".format(link.get('src'))

		img_counter += 1

		img_global_counter += 1
		img_array.append(img_global_counter)

		try:
			save_in_folder(post_global_counter, img_global_counter, href, title_translaterate, title_translaterate, img_counter)
		except:
			img_counter -= 1

			img_global_counter -= 1
			img_array.remove(img_global_counter)
			continue


	sql_global.write(sql_template(replace_single_quote(clear_white_space(title, '\n', 0)), title_translaterate, post_global_counter, img_array, replace_single_quote(clear_white_space(content_text, '\s', 3))))

	return img_counter


def translaterate(text): #Russian text from "Привет, мир!" to "privet-mir"
	text = transliterate.translit(text, reversed=True) # from "Привет, мир!" to "Privet, mir!"
	
	clean_text = clear_text(text) # from "Privet, mir!" to "Privet mir"

	clean_text = '-'.join(clean_text.lower().split(' ')) # from "Privet mir" to "privet-mir"
	return clean_text


def clear_text(text): # Clear text from messy symbols 
	reg = re.compile('[^а-яА-Яa-zA-Z0-9 ]')
	text = reg.sub('', text)
	return text


def clear_white_space(text, method, num_of_space): # Clear white space 
	reg = re.compile(r"(?m)%s{%s,}" % (method, num_of_space))
	text = reg.sub('', text)
	return text


def try_except(text_node_class, soup): # Avoiding error with absent text on some pages
	try:
		text = soup.select_one(text_node_class).get_text()
	except AttributeError:
		text = ""
	
	return text


def replace_single_quote(text): # Avoiding SQL single quote INSERT error
	text = text.replace("'", "''")

	return text


def save_in_folder(post_global_counter, img_global_counter, file_link, folder_name, file_name, img_counter): # Save img in page related folder
	filename = 'c:/users/симеон/desktop/py_parser/{}-{}/{}-{}-{}.jpg'.format(post_global_counter, folder_name, img_global_counter, file_name, img_counter)
	folder_name = os.path.dirname(filename)
	if not os.path.exists(folder_name):
		os.makedirs(folder_name)

	urllib2.urlretrieve(file_link, filename)
	save_global(img_global_counter, file_link, file_name, img_counter)


def save_global(img_global_counter, file_link, file_name, img_counter): # Save img in stock folder
	filename = 'c:/users/симеон/desktop/py_parser/1-ALL-IMG/{}-{}-{}.jpg'.format(img_global_counter, file_name,	img_counter)
	folder_name = os.path.dirname(filename)
	if not os.path.exists(folder_name):
		os.makedirs(folder_name)

	urllib2.urlretrieve(file_link, filename)


def sql_template(post_title, post_name, post_global_counter, img_array, content_text): # building SQL-request for new page
	
	# Create content with right amount if images
	content_inner = """
	[vc_row]
		[vc_column]
			[vc_row_inner]
				[vc_column_inner width="1/2"]
					[vc_single_image image="{}" img_size="full" alignment="center" onclick="link_image"]
				[/vc_column_inner]
				[vc_column_inner width="1/2"]
					[vc_column_text]
						{}
					[/vc_column_text]
				[/vc_column_inner]
			[/vc_row_inner]
			[vc_empty_space height="40px"]
			[vc_custom_heading text="ВЫПОЛНЕННЫЕ РАБОТЫ" font_container="tag:h2|text_align:left|color:%230079ce" use_theme_fonts="yes" css=".vc_custom_1538483422586{{border-left-width: 3px !important;padding-left: 15px !important;border-left-color: #0079ce !important;border-left-style: solid !important;}}"]
			[vc_empty_space height="35px"]
			[ultimate_carousel slides_on_desk="2" slides_on_tabs="2" slides_on_mob="1" autoplay="off" next_icon="ultsl-arrow-right6" prev_icon="ultsl-arrow-left6" dots_icon="ultsl-radio-unchecked"]
	""".format(img_array[0], content_text)

	for img_id in img_array[1:]:
		content_inner += """
					[vc_single_image image="{}" img_size="full" alignment="center" onclick="link_image"]
		""".format(img_id)

	content_inner += """
			[/ultimate_carousel]
			[vc_empty_space height="15px"]
		[/vc_column]
	[/vc_row]
	"""

	# Create SQL-request with all variables (to wptg_posts and wptg_term_relationships)
	sql_request = """
	INSERT INTO wptg_posts (post_author,
							post_date,
							post_date_gmt,
							post_modified,
							post_modified_gmt,
							post_title, 
							post_status, 
							post_name,
							comment_status,
							ping_status,
							post_type,
							post_content) 
	VALUES (1,
			'2018-11-18', 
			'2018-11-18', 
			'2018-11-18', 
			'2018-11-18', 
			'{}',
			'publish', 
			'{}',
			'closed',
			'closed',
			'post',
			'{}');
	""".format(post_title, post_name, content_inner)

	return sql_request


if __name__ == '__main__':
	main(str(input("Write in site's categoty link: "))) # link of sites categoty page