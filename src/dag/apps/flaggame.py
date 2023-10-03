import dag
from dag import r_
import pycountry

COUNTRIESDICT = {"Afghanistan": "AFG", "Albania": "ALB", "Algeria": "DZA", "Andorra": "AND", "Angola": "AGO", "Antigua and Barbuda": "ATG", "Argentina": "ARG", "Armenia": "ARM", "Aruba": "ABW", "Australia": "AUS", "Austria": "AUT", "Azerbaijan": "AZE", "Bahamas (the)": "BHS", "Bahrain": "BHR", "Bangladesh": "BGD", "Barbados": "BRB", "Belarus": "BLR", "Belgium": "BEL", "Belize": "BLZ", "Benin": "BEN", "Bermuda": "BMU", "Bhutan": "BTN", "Bolivia (Plurinational State of)": "BOL", "Bosnia and Herzegovina": "BIH", "Botswana": "BWA", "Brazil": "BRA", "Brunei Darussalam": "BRN", "Bulgaria": "BGR", "Burkina Faso": "BFA", "Burundi": "BDI", "Cabo Verde / Cape Verde": "CPV", "Cambodia": "KHM", "Cameroon": "CMR", "Canada": "CAN", "Central African Republic (the)": "CAF", "Chad": "TCD", "Chile": "CHL", "China": "CHN",  "Colombia": "COL", "Comoros (the)": "COM", "Congo (the Democratic Republic of the) / drc": "COD", "Congo (the)": "COG", "Costa Rica": "CRI", "Côte d'Ivoire / Ivory Coast": "CIV", "Croatia": "HRV", "Cuba": "CUB", "Cyprus": "CYP", "Czechia / Czech republic": "CZE", "Denmark": "DNK", "Djibouti": "DJI", "Dominica": "DMA", "Dominican Republic (the)": "DOM", "Ecuador": "ECU", "Egypt": "EGY", "El Salvador": "SLV", "Equatorial Guinea": "GNQ", "Eritrea": "ERI", "Estonia": "EST", "Eswatini / Swaziland ": "SWZ", "Ethiopia": "ETH", "Fiji": "FJI", "Finland": "FIN", "France": "FRA", "French Guiana": "GUF", "Gabon": "GAB", "Gambia (the)": "GMB", "Georgia": "GEO", "Germany": "DEU", "Ghana": "GHA", "Greece": "GRC", "Greenland": "GRL", "Grenada": "GRD", "Guatemala": "GTM", "Guinea": "GIN", "Guinea-Bissau": "GNB", "Guyana": "GUY", "Haiti": "HTI", "Holy See (the) / Vatican": "VAT", "Honduras": "HND", "Hong Kong": "HKG", "Hungary": "HUN", "Iceland": "ISL", "India": "IND", "Indonesia": "IDN", "Iran (Islamic Republic of)": "IRN", "Iraq": "IRQ", "Ireland": "IRL", "Israel": "ISR", "Italy": "ITA", "Jamaica": "JAM", "Japan": "JPN", "Jordan": "JOR", "Kazakhstan": "KAZ", "Kenya": "KEN", "Kiribati": "KIR", "Korea (the Democratic People's Republic of) / North Korea": "PRK", "Korea (the Republic of) / South Korea": "KOR", "Kuwait": "KWT", "Kyrgyzstan": "KGZ", "Lao People's Democratic Republic (the)": "LAO", "Latvia": "LVA", "Lebanon": "LBN", "Lesotho": "LSO", "Liberia": "LBR", "Libya": "LBY", "Liechtenstein": "LIE", "Lithuania": "LTU", "Luxembourg": "LUX", "Macao": "MAC", "Republic of North Macedonia": "MKD", "Madagascar": "MDG", "Malawi": "MWI", "Malaysia": "MYS", "Maldives": "MDV", "Mali": "MLI", "Malta": "MLT", "Marshall Islands (the)": "MHL", "Martinique": "MTQ", "Mauritania": "MRT", "Mauritius": "MUS", "Mexico": "MEX", "Micronesia (Federated States of)": "FSM", "Moldova (the Republic of)": "MDA", "Monaco": "MCO", "Mongolia": "MNG", "Montenegro": "MNE", "Montserrat": "MSR", "Morocco": "MAR", "Mozambique": "MOZ", "Myanmar": "MMR", "Namibia": "NAM", "Nauru": "NRU", "Nepal": "NPL", "Netherlands (the)": "NLD", "New Zealand": "NZL", "Nicaragua": "NIC", "Niger (the)": "NER", "Nigeria": "NGA", "Norway": "NOR", "Oman": "OMN", "Pakistan": "PAK", "Palau": "PLW", "Palestine, State of": "PSE", "Panama": "PAN", "Papua New Guinea": "PNG", "Paraguay": "PRY", "Peru": "PER", "Philippines (the)": "PHL", "Poland": "POL", "Portugal": "PRT", "Qatar": "QAT", "Romania": "ROU", "Russian Federation (the)": "RUS", "Rwanda": "RWA", "Saint Kitts and Nevis": "KNA", "Saint Lucia": "LCA", "Saint Vincent and the Grenadines": "VCT", "Samoa": "WSM", "San Marino": "SMR", "Sao Tome and Principe": "STP", "Saudi Arabia": "SAU", "Senegal": "SEN", "Serbia": "SRB", "Seychelles": "SYC", "Sierra Leone": "SLE", "Singapore": "SGP", "Slovakia": "SVK", "Slovenia": "SVN", "Solomon Islands": "SLB", "Somalia": "SOM", "South Africa": "ZAF", "South Sudan": "SSD", "Spain": "ESP", "Sri Lanka": "LKA", "Sudan (the)": "SDN", "Suriname": "SUR", "Sweden": "SWE", "Switzerland": "CHE", "Syrian Arab Republic": "SYR", "Taiwan (Province of China)": "TWN", "Tajikistan": "TJK", "Tanzania, United Republic of": "TZA", "Thailand": "THA", "Timor-Leste": "TLS", "Togo": "TGO", "Tonga": "TON", "Trinidad and Tobago": "TTO", "Tunisia": "TUN", "Turkey": "TUR", "Turkmenistan": "TKM", "Tuvalu": "TUV", "Uganda": "UGA", "Ukraine": "UKR", "United Arab Emirates (the) / UAE": "ARE", "United Kingdom of Great Britain and Northern Ireland (the) / UK": "GBR", "United States of America (the)": "USA", "Uruguay": "URY", "Uzbekistan": "UZB", "Vanuatu": "VUT", "Venezuela (Bolivarian Republic of)": "VEN", "Viet Nam / Vietnam": "VNM", "Western Sahara": "ESH", "Yemen": "YEM", "Zambia": "ZMB", "Zimbabwe": "ZWE"}

REGIONS = [*pycountry.countries]
COUNTRIES = [r for r in REGIONS if r.alpha_3 in COUNTRIESDICT.values()]


flaggame = dag.app("flaggame", baseurl = "https://flagcdn.com/")


countries = flaggame.collection.NO_CACHE("countries", value = COUNTRIES)
countries.resources.label(r_.name)


@flaggame.cmd
def flags():
	dag.get.CACHE.BYTES([f"h40/{c.alpha_2.lower()}.png" for c in COUNTRIES])


@flaggame.arg.Flag("--guess", target = "do_guess")
@flaggame.DEFAULT.cmd
def game(country = None, do_guess = False):
	origcountry = country
	is_empty_active = False

	total = -1
	correct = 0
	streak = 0
	maxstreak = 0

	countrylist = countries()

	with dag.passexc(EOFError):
		# Cycle countries
		while countrylist:
			total += 1

			if not origcountry:
				oldcountry = country

				while oldcountry == country:
					country = countrylist.random()

			cc = country._response._data

			flag = dag.get.CACHE.BYTES(f"h40/{cc.alpha_2.lower()}.png")

			# Cycle guesses

			tries = 1
			while True:
				dag.echo(dag.img(flag).to_cli(maxheight = 30, cropbbox = False))

				if origcountry and not do_guess:
					return cc

				guess = dag.cli.prompt(f"Country name {correct}/{total} ({correct*100/total if total else 0:.2f}%). Tries = {tries}. Streak = {streak} (max {maxstreak}). # Left = {len(countrylist)}", complete_list = countries().choices(), display_choices = False, killdelims = " ", id = "flaggame-guess")

				if not tries == 1:
					streak = 0

				tries += 1

				if not guess:
					streak = 0
					dag.echo(f"<c red u>{cc}</c>\n\n")
					if is_empty_active:
						return

					is_empty_active = True
					continue

				is_empty_active = False

				if (len(guess) >= 2 and guess[0] == guess[1]) or len(guess) == 1:
					return cc

				if guess.lower() in cc.name.lower():
					if tries == 2:
						correct += 1
						streak += 1
						maxstreak = max(streak, maxstreak)
						countrylist -= country
					else:
						streak = 0

					dag.echo(f"<c red u>{cc}</c>\n\n")
					break

				streak = 0
	return cc