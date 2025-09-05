from pprint import pprint

REGIONS = {
    "002": {
        "name": "Africa",
        "parent": "001"
    },
    "015": {
        "name": "North Africa",
        "parent": "002"
    },
    "011": {
        "name": "West Africa",
        "parent": "002"
    },
    "017": {
        "name": "Central Africa",
        "parent": "002"
    },
    "014": {
        "name": "Eastern Africa",
        "parent": "002"
    },
    "018": {
        "name": "Southern Africa",
        "parent": "002"
    },
    "150": {
        "name": "Europe",
        "parent": "001"
    },
    "154": {
        "name": "Northern Europe",
        "parent": "150"
    },
    "155": {
        "name": "Western Europe",
        "parent": "150"
    },
    "EUE": {
        "name": "European Union",
        "parent": "150"
    },
    "151": {
        "name": "Eastern Europe",
        "parent": "150"
    },
    "039": {
        "name": "Southern Europe",
        "parent": "150"
    },
    "019": {
        "name": "Americas",
        "parent": "001"
    },
    "005": {
        "name": "South America",
        "parent": "001"
    },
    "003": {
        "name": "North America",
        "parent": "001"
    },
    "021": {
        "name": "Northern America",
        "parent": "019"
    },
    "013": {
        "name": "Central America",
        "parent": "019"
    },
    "029": {
        "name": "Caribbean",
        "parent": "019"
    },
    "142": {
        "name": "Asia",
        "parent": "001"
    },
    "030": {
        "name": "Eastern Asia",
        "parent": "142"
    },
    "034": {
        "name": "Southern Asia",
        "parent": "142"
    },
    "035": {
        "name": "South-Eastern Asia",
        "parent": "142"
    },
    "143": {
        "name": "Central Asia",
        "parent": "142"
    },
    "145": {
        "name": "Western Asia",
        "parent": "142"
    },
    "009": {
        "name": "Oceania",
        "parent": "001"
    },
    "053": {
        "name": "Australia and New Zealand",
        "parent": "009"
    },
    "054": {
        "name": "Melanesia",
        "parent": "009"
    },
    "057": {
        "name": "Micronesia",
        "parent": "009"
    },
    "061": {
        "name": "Polynesia",
        "parent": "009"
    },
    "001": {
        "name": "World"
    },
    "010": {
        "name": "Antarctica",
        "parent": "001"
    }
}

COUNTRIES = {
    'ABW': {
        'alpha2': 'AW',
        'alpha3': 'ABW',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:AW',
        'name': 'Aruba',
        'code': '533',
        'region': '029'
    },
    'AFG': {
        'alpha2': 'AF',
        'alpha3': 'AFG',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:AF',
        'name': 'Afghanistan',
        'code': '004',
        'region': '034'
    },
    'AGO': {
        'alpha2': 'AO',
        'alpha3': 'AGO',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:AO',
        'name': 'Angola',
        'code': '024',
        'region': '017'
    },
    'AIA': {
        'alpha2': 'AI',
        'alpha3': 'AIA',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:AI',
        'name': 'Anguilla',
        'code': '660',
        'region': '029'
    },
    'ALA': {
        'alpha2': 'AX',
        'alpha3': 'ALA',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:AX',
        'name': 'Åland Islands',
        'code': '248',
        'region': '154'
    },
    'ALB': {
        'alpha2': 'AL',
        'alpha3': 'ALB',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:AL',
        'name': 'Albania',
        'code': '008',
        'region': '039'
    },
    'AND': {
        'alpha2': 'AD',
        'alpha3': 'AND',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:AD',
        'name': 'Andorra',
        'code': '020',
        'region': '039'
    },
    'ARE': {
        'alpha2': 'AE',
        'alpha3': 'ARE',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:AE',
        'name': 'United Arab Emirates',
        'code': '784',
        'region': '145'
    },
    'ARG': {
        'alpha2': 'AR',
        'alpha3': 'ARG',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:AR',
        'name': 'Argentina',
        'code': '032',
        'region': '005'
    },
    'ARM': {
        'alpha2': 'AM',
        'alpha3': 'ARM',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:AM',
        'name': 'Armenia',
        'code': '051',
        'region': '145'
    },
    'ASM': {
        'alpha2': 'AS',
        'alpha3': 'ASM',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:AS',
        'name': 'American Samoa',
        'code': '016',
        'region': '061'
    },
    'ATA': {
        'alpha2': 'AQ',
        'alpha3': 'ATA',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:AQ',
        'name': 'Antarctica',
        'code': '010',
        'region': None
    },
    'ATF': {
        'alpha2': 'TF',
        'alpha3': 'ATF',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:TF',
        'name': 'French Southern Territories',
        'code': '260',
        'region': None
    },
    'ATG': {
        'alpha2': 'AG',
        'alpha3': 'ATG',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:AG',
        'name': 'Antigua and Barbuda',
        'code': '028',
        'region': '029'
    },
    'AUS': {
        'alpha2': 'AU',
        'alpha3': 'AUS',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:AU',
        'name': 'Australia',
        'code': '036',
        'region': '053'
    },
    'AUT': {
        'alpha2': 'AT',
        'alpha3': 'AUT',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:AT',
        'name': 'Austria',
        'code': '040',
        'region': '155'
    },
    'AZE': {
        'alpha2': 'AZ',
        'alpha3': 'AZE',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:AZ',
        'name': 'Azerbaijan',
        'code': '031',
        'region': '145'
    },
    'BDI': {
        'alpha2': 'BI',
        'alpha3': 'BDI',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:BI',
        'name': 'Burundi',
        'code': '108',
        'region': '014'
    },
    'BEL': {
        'alpha2': 'BE',
        'alpha3': 'BEL',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:BE',
        'name': 'Belgium',
        'code': '056',
        'region': '155'
    },
    'BEN': {
        'alpha2': 'BJ',
        'alpha3': 'BEN',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:BJ',
        'name': 'Benin',
        'code': '204',
        'region': '011'
    },
    'BES': {
        'alpha2': 'BQ',
        'alpha3': 'BES',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:BQ',
        'name': 'Bonaire,  Sint Eustatius and Saba',
        'code': '535',
        'region': '029'
    },
    'BFA': {
        'alpha2': 'BF',
        'alpha3': 'BFA',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:BF',
        'name': 'Burkina Faso',
        'code': '854',
        'region': '011'
    },
    'BGD': {
        'alpha2': 'BD',
        'alpha3': 'BGD',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:BD',
        'name': 'Bangladesh',
        'code': '050',
        'region': '034'
    },
    'BGR': {
        'alpha2': 'BG',
        'alpha3': 'BGR',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:BG',
        'name': 'Bulgaria',
        'code': '100',
        'region': '151'
    },
    'BHR': {
        'alpha2': 'BH',
        'alpha3': 'BHR',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:BH',
        'name': 'Bahrain',
        'code': '048',
        'region': '145'
    },
    'BHS': {
        'alpha2': 'BS',
        'alpha3': 'BHS',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:BS',
        'name': 'Bahamas',
        'code': '044',
        'region': '029'
    },
    'BIH': {
        'alpha2': 'BA',
        'alpha3': 'BIH',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:BA',
        'name': 'Bosnia and Herzegovina',
        'code': '070',
        'region': '039'
    },
    'BLM': {
        'alpha2': 'BL',
        'alpha3': 'BLM',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:BL',
        'name': 'Saint Barthélemy',
        'code': '652',
        'region': '029'
    },
    'BLR': {
        'alpha2': 'BY',
        'alpha3': 'BLR',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:BY',
        'name': 'Belarus',
        'code': '112',
        'region': '151'
    },
    'BLZ': {
        'alpha2': 'BZ',
        'alpha3': 'BLZ',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:BZ',
        'name': 'Belize',
        'code': '084',
        'region': '013'
    },
    'BMU': {
        'alpha2': 'BM',
        'alpha3': 'BMU',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:BM',
        'name': 'Bermuda',
        'code': '060',
        'region': '021'
    },
    'BOL': {
        'alpha2': 'BO',
        'alpha3': 'BOL',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:BO',
        'name': 'Bolivia',
        'code': '068',
        'region': '005'
    },
    'BRA': {
        'alpha2': 'BR',
        'alpha3': 'BRA',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:BR',
        'name': 'Brazil',
        'code': '076',
        'region': '005'
    },
    'BRB': {
        'alpha2': 'BB',
        'alpha3': 'BRB',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:BB',
        'name': 'Barbados',
        'code': '052',
        'region': '029'
    },
    'BRN': {
        'alpha2': 'BN',
        'alpha3': 'BRN',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:BN',
        'name': 'Brunei Darussalam',
        'code': '096',
        'region': '035'
    },
    'BTN': {
        'alpha2': 'BT',
        'alpha3': 'BTN',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:BT',
        'name': 'Bhutan',
        'code': '064',
        'region': '034'
    },
    'BVT': {
        'alpha2': 'BV',
        'alpha3': 'BVT',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:BV',
        'name': 'Bouvet Island',
        'code': '074',
        'region': None
    },
    'BWA': {
        'alpha2': 'BW',
        'alpha3': 'BWA',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:BW',
        'name': 'Botswana',
        'code': '072',
        'region': '018'
    },
    'CAF': {
        'alpha2': 'CF',
        'alpha3': 'CAF',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:CF',
        'name': 'Central African Republic',
        'code': '140',
        'region': '017'
    },
    'CAN': {
        'alpha2': 'CA',
        'alpha3': 'CAN',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:CA',
        'name': 'Canada',
        'code': '124',
        'region': '021'
    },
    'CCK': {
        'alpha2': 'CC',
        'alpha3': 'CCK',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:CC',
        'name': 'Cocos Islands',
        'code': '166',
        'region': None
    },
    'CHE': {
        'alpha2': 'CH',
        'alpha3': 'CHE',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:CH',
        'name': 'Switzerland',
        'code': '756',
        'region': '155'
    },
    'CHL': {
        'alpha2': 'CL',
        'alpha3': 'CHL',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:CL',
        'name': 'Chile',
        'code': '152',
        'region': '005'
    },
    'CHN': {
        'alpha2': 'CN',
        'alpha3': 'CHN',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:CN',
        'name': 'China',
        'code': '156',
        'region': '030'
    },
    'CIV': {
        'alpha2': 'CI',
        'alpha3': 'CIV',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:CI',
        'name': "Côte d'Ivoire",
        'code': '384',
        'region': '011'
    },
    'CMR': {
        'alpha2': 'CM',
        'alpha3': 'CMR',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:CM',
        'name': 'Cameroon',
        'code': '120',
        'region': '017'
    },
    'COD': {
        'alpha2': 'CD',
        'alpha3': 'COD',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:CD',
        'name': 'Congo,  Democratic Republic of the',
        'code': '180',
        'region': '017'
    },
    'COG': {
        'alpha2': 'CG',
        'alpha3': 'COG',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:CG',
        'name': 'Congo',
        'code': '178',
        'region': '017'
    },
    'COK': {
        'alpha2': 'CK',
        'alpha3': 'COK',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:CK',
        'name': 'Cook Islands',
        'code': '184',
        'region': '061'
    },
    'COL': {
        'alpha2': 'CO',
        'alpha3': 'COL',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:CO',
        'name': 'Colombia',
        'code': '170',
        'region': '005'
    },
    'COM': {
        'alpha2': 'KM',
        'alpha3': 'COM',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:KM',
        'name': 'Comoros',
        'code': '174',
        'region': '014'
    },
    'CPV': {
        'alpha2': 'CV',
        'alpha3': 'CPV',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:CV',
        'name': 'Cabo Verde',
        'code': '132',
        'region': '011'
    },
    'CRI': {
        'alpha2': 'CR',
        'alpha3': 'CRI',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:CR',
        'name': 'Costa Rica',
        'code': '188',
        'region': '013'
    },
    'CUB': {
        'alpha2': 'CU',
        'alpha3': 'CUB',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:CU',
        'name': 'Cuba',
        'code': '192',
        'region': '029'
    },
    'CUW': {
        'alpha2': 'CW',
        'alpha3': 'CUW',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:CW',
        'name': 'Curaçao',
        'code': '531',
        'region': '029'
    },
    'CXR': {
        'alpha2': 'CX',
        'alpha3': 'CXR',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:CX',
        'name': 'Christmas Island',
        'code': '162',
        'region': None
    },
    'CYM': {
        'alpha2': 'KY',
        'alpha3': 'CYM',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:KY',
        'name': 'Cayman Islands',
        'code': '136',
        'region': '029'
    },
    'CYP': {
        'alpha2': 'CY',
        'alpha3': 'CYP',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:CY',
        'name': 'Cyprus',
        'code': '196',
        'region': '145'
    },
    'CZE': {
        'alpha2': 'CZ',
        'alpha3': 'CZE',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:CZ',
        'name': 'Czech Republic',
        'code': '203',
        'region': '151'
    },
    'DEU': {
        'alpha2': 'DE',
        'alpha3': 'DEU',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:DE',
        'name': 'Germany',
        'code': '276',
        'region': '155'
    },
    'DJI': {
        'alpha2': 'DJ',
        'alpha3': 'DJI',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:DJ',
        'name': 'Djibouti',
        'code': '262',
        'region': '014'
    },
    'DMA': {
        'alpha2': 'DM',
        'alpha3': 'DMA',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:DM',
        'name': 'Dominica',
        'code': '212',
        'region': '029'
    },
    'DNK': {
        'alpha2': 'DK',
        'alpha3': 'DNK',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:DK',
        'name': 'Denmark',
        'code': '208',
        'region': '154'
    },
    'DOM': {
        'alpha2': 'DO',
        'alpha3': 'DOM',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:DO',
        'name': 'Dominican Republic',
        'code': '214',
        'region': '029'
    },
    'DZA': {
        'alpha2': 'DZ',
        'alpha3': 'DZA',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:DZ',
        'name': 'Algeria',
        'code': '012',
        'region': '015'
    },
    'ECU': {
        'alpha2': 'EC',
        'alpha3': 'ECU',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:EC',
        'name': 'Ecuador',
        'code': '218',
        'region': '005'
    },
    'EGY': {
        'alpha2': 'EG',
        'alpha3': 'EGY',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:EG',
        'name': 'Egypt',
        'code': '818',
        'region': '015'
    },
    'ERI': {
        'alpha2': 'ER',
        'alpha3': 'ERI',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:ER',
        'name': 'Eritrea',
        'code': '232',
        'region': '014'
    },
    'ESH': {
        'alpha2': 'EH',
        'alpha3': 'ESH',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:EH',
        'name': 'Western Sahara',
        'code': '732',
        'region': '015'
    },
    'ESP': {
        'alpha2': 'ES',
        'alpha3': 'ESP',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:ES',
        'name': 'Spain',
        'code': '724',
        'region': '039'
    },
    'EST': {
        'alpha2': 'EE',
        'alpha3': 'EST',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:EE',
        'name': 'Estonia',
        'code': '233',
        'region': '154'
    },
    'ETH': {
        'alpha2': 'ET',
        'alpha3': 'ETH',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:ET',
        'name': 'Ethiopia',
        'code': '231',
        'region': '014'
    },
    'FIN': {
        'alpha2': 'FI',
        'alpha3': 'FIN',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:FI',
        'name': 'Finland',
        'code': '246',
        'region': '154'
    },
    'FJI': {
        'alpha2': 'FJ',
        'alpha3': 'FJI',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:FJ',
        'name': 'Fiji',
        'code': '242',
        'region': '054'
    },
    'FLK': {
        'alpha2': 'FK',
        'alpha3': 'FLK',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:FK',
        'name': 'Falkland Islands',
        'code': '238',
        'region': '005'
    },
    'FRA': {
        'alpha2': 'FR',
        'alpha3': 'FRA',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:FR',
        'name': 'France',
        'code': '250',
        'region': '155'
    },
    'FRO': {
        'alpha2': 'FO',
        'alpha3': 'FRO',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:FO',
        'name': 'Faroe Islands',
        'code': '234',
        'region': '154'
    },
    'FSM': {
        'alpha2': 'FM',
        'alpha3': 'FSM',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:FM',
        'name': 'Micronesia',
        'code': '583',
        'region': '057'
    },
    'GAB': {
        'alpha2': 'GA',
        'alpha3': 'GAB',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:GA',
        'name': 'Gabon',
        'code': '266',
        'region': '017'
    },
    'GBR': {
        'alpha2': 'GB',
        'alpha3': 'GBR',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:GB',
        'name': 'United Kingdom',
        'code': '826',
        'region': '154'
    },
    'GEO': {
        'alpha2': 'GE',
        'alpha3': 'GEO',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:GE',
        'name': 'Georgia',
        'code': '268',
        'region': '145'
    },
    'GGY': {
        'alpha2': 'GG',
        'alpha3': 'GGY',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:GG',
        'name': 'Guernsey',
        'code': '831',
        'region': '154'
    },
    'GHA': {
        'alpha2': 'GH',
        'alpha3': 'GHA',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:GH',
        'name': 'Ghana',
        'code': '288',
        'region': '011'
    },
    'GIB': {
        'alpha2': 'GI',
        'alpha3': 'GIB',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:GI',
        'name': 'Gibraltar',
        'code': '292',
        'region': '039'
    },
    'GIN': {
        'alpha2': 'GN',
        'alpha3': 'GIN',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:GN',
        'name': 'Guinea',
        'code': '324',
        'region': '011'
    },
    'GLP': {
        'alpha2': 'GP',
        'alpha3': 'GLP',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:GP',
        'name': 'Guadeloupe',
        'code': '312',
        'region': '029'
    },
    'GMB': {
        'alpha2': 'GM',
        'alpha3': 'GMB',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:GM',
        'name': 'Gambia',
        'code': '270',
        'region': '011'
    },
    'GNB': {
        'alpha2': 'GW',
        'alpha3': 'GNB',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:GW',
        'name': 'Guinea-Bissau',
        'code': '624',
        'region': '011'
    },
    'GNQ': {
        'alpha2': 'GQ',
        'alpha3': 'GNQ',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:GQ',
        'name': 'Equatorial Guinea',
        'code': '226',
        'region': '017'
    },
    'GRC': {
        'alpha2': 'GR',
        'alpha3': 'GRC',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:GR',
        'name': 'Greece',
        'code': '300',
        'region': '039'
    },
    'GRD': {
        'alpha2': 'GD',
        'alpha3': 'GRD',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:GD',
        'name': 'Grenada',
        'code': '308',
        'region': '029'
    },
    'GRL': {
        'alpha2': 'GL',
        'alpha3': 'GRL',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:GL',
        'name': 'Greenland',
        'code': '304',
        'region': '021'
    },
    'GTM': {
        'alpha2': 'GT',
        'alpha3': 'GTM',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:GT',
        'name': 'Guatemala',
        'code': '320',
        'region': '013'
    },
    'GUF': {
        'alpha2': 'GF',
        'alpha3': 'GUF',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:GF',
        'name': 'French Guiana',
        'code': '254',
        'region': '005'
    },
    'GUM': {
        'alpha2': 'GU',
        'alpha3': 'GUM',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:GU',
        'name': 'Guam',
        'code': '316',
        'region': '057'
    },
    'GUY': {
        'alpha2': 'GY',
        'alpha3': 'GUY',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:GY',
        'name': 'Guyana',
        'code': '328',
        'region': '005'
    },
    'HKG': {
        'alpha2': 'HK',
        'alpha3': 'HKG',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:HK',
        'name': 'Hong Kong',
        'code': '344',
        'region': '030'
    },
    'HMD': {
        'alpha2': 'HM',
        'alpha3': 'HMD',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:HM',
        'name': 'Heard and McDonald Islands',
        'code': '334',
        'region': None
    },
    'HND': {
        'alpha2': 'HN',
        'alpha3': 'HND',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:HN',
        'name': 'Honduras',
        'code': '340',
        'region': '013'
    },
    'HRV': {
        'alpha2': 'HR',
        'alpha3': 'HRV',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:HR',
        'name': 'Croatia',
        'code': '191',
        'region': '039'
    },
    'HTI': {
        'alpha2': 'HT',
        'alpha3': 'HTI',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:HT',
        'name': 'Haiti',
        'code': '332',
        'region': '029'
    },
    'HUN': {
        'alpha2': 'HU',
        'alpha3': 'HUN',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:HU',
        'name': 'Hungary',
        'code': '348',
        'region': '151'
    },
    'IDN': {
        'alpha2': 'ID',
        'alpha3': 'IDN',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:ID',
        'name': 'Indonesia',
        'code': '360',
        'region': '035'
    },
    'IMN': {
        'alpha2': 'IM',
        'alpha3': 'IMN',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:IM',
        'name': 'Isle of Man',
        'code': '833',
        'region': '154'
    },
    'IND': {
        'alpha2': 'IN',
        'alpha3': 'IND',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:IN',
        'name': 'India',
        'code': '356',
        'region': '034'
    },
    'IOT': {
        'alpha2': 'IO',
        'alpha3': 'IOT',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:IO',
        'name': 'British Indian Ocean Territory',
        'code': '086',
        'region': None
    },
    'IRL': {
        'alpha2': 'IE',
        'alpha3': 'IRL',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:IE',
        'name': 'Ireland',
        'code': '372',
        'region': '154'
    },
    'IRN': {
        'alpha2': 'IR',
        'alpha3': 'IRN',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:IR',
        'name': 'Iran',
        'code': '364',
        'region': '034'
    },
    'IRQ': {
        'alpha2': 'IQ',
        'alpha3': 'IRQ',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:IQ',
        'name': 'Iraq',
        'code': '368',
        'region': '145'
    },
    'ISL': {
        'alpha2': 'IS',
        'alpha3': 'ISL',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:IS',
        'name': 'Iceland',
        'code': '352',
        'region': '154'
    },
    'ISR': {
        'alpha2': 'IL',
        'alpha3': 'ISR',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:IL',
        'name': 'Israel',
        'code': '376',
        'region': '145'
    },
    'ITA': {
        'alpha2': 'IT',
        'alpha3': 'ITA',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:IT',
        'name': 'Italy',
        'code': '380',
        'region': '039'
    },
    'JAM': {
        'alpha2': 'JM',
        'alpha3': 'JAM',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:JM',
        'name': 'Jamaica',
        'code': '388',
        'region': '029'
    },
    'JEY': {
        'alpha2': 'JE',
        'alpha3': 'JEY',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:JE',
        'name': 'Jersey',
        'code': '832',
        'region': '154'
    },
    'JOR': {
        'alpha2': 'JO',
        'alpha3': 'JOR',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:JO',
        'name': 'Jordan',
        'code': '400',
        'region': '145'
    },
    'JPN': {
        'alpha2': 'JP',
        'alpha3': 'JPN',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:JP',
        'name': 'Japan',
        'code': '392',
        'region': '030'
    },
    'KAZ': {
        'alpha2': 'KZ',
        'alpha3': 'KAZ',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:KZ',
        'name': 'Kazakhstan',
        'code': '398',
        'region': '143'
    },
    'KEN': {
        'alpha2': 'KE',
        'alpha3': 'KEN',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:KE',
        'name': 'Kenya',
        'code': '404',
        'region': '014'
    },
    'KGZ': {
        'alpha2': 'KG',
        'alpha3': 'KGZ',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:KG',
        'name': 'Kyrgyzstan',
        'code': '417',
        'region': '143'
    },
    'KHM': {
        'alpha2': 'KH',
        'alpha3': 'KHM',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:KH',
        'name': 'Cambodia',
        'code': '116',
        'region': '035'
    },
    'KIR': {
        'alpha2': 'KI',
        'alpha3': 'KIR',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:KI',
        'name': 'Kiribati',
        'code': '296',
        'region': '057'
    },
    'KNA': {
        'alpha2': 'KN',
        'alpha3': 'KNA',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:KN',
        'name': 'Saint Kitts and Nevis',
        'code': '659',
        'region': '029'
    },
    'KOR': {
        'alpha2': 'KR',
        'alpha3': 'KOR',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:KR',
        'name': 'South Korea',
        'code': '410',
        'region': '030'
    },
    'KWT': {
        'alpha2': 'KW',
        'alpha3': 'KWT',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:KW',
        'name': 'Kuwait',
        'code': '414',
        'region': '145'
    },
    'LAO': {
        'alpha2': 'LA',
        'alpha3': 'LAO',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:LA',
        'name': "Lao People's Democratic Republic",
        'code': '418',
        'region': '035'
    },
    'LBN': {
        'alpha2': 'LB',
        'alpha3': 'LBN',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:LB',
        'name': 'Lebanon',
        'code': '422',
        'region': '145'
    },
    'LBR': {
        'alpha2': 'LR',
        'alpha3': 'LBR',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:LR',
        'name': 'Liberia',
        'code': '430',
        'region': '011'
    },
    'LBY': {
        'alpha2': 'LY',
        'alpha3': 'LBY',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:LY',
        'name': 'Libya',
        'code': '434',
        'region': '015'
    },
    'LCA': {
        'alpha2': 'LC',
        'alpha3': 'LCA',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:LC',
        'name': 'Saint Lucia',
        'code': '662',
        'region': '029'
    },
    'LIE': {
        'alpha2': 'LI',
        'alpha3': 'LIE',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:LI',
        'name': 'Liechtenstein',
        'code': '438',
        'region': '155'
    },
    'LKA': {
        'alpha2': 'LK',
        'alpha3': 'LKA',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:LK',
        'name': 'Sri Lanka',
        'code': '144',
        'region': '034'
    },
    'LSO': {
        'alpha2': 'LS',
        'alpha3': 'LSO',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:LS',
        'name': 'Lesotho',
        'code': '426',
        'region': '018'
    },
    'LTU': {
        'alpha2': 'LT',
        'alpha3': 'LTU',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:LT',
        'name': 'Lithuania',
        'code': '440',
        'region': '154'
    },
    'LUX': {
        'alpha2': 'LU',
        'alpha3': 'LUX',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:LU',
        'name': 'Luxembourg',
        'code': '442',
        'region': '155'
    },
    'LVA': {
        'alpha2': 'LV',
        'alpha3': 'LVA',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:LV',
        'name': 'Latvia',
        'code': '428',
        'region': '154'
    },
    'MAC': {
        'alpha2': 'MO',
        'alpha3': 'MAC',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:MO',
        'name': 'Macao',
        'code': '446',
        'region': '030'
    },
    'MAF': {
        'alpha2': 'MF',
        'alpha3': 'MAF',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:MF',
        'name': 'Saint Martin (French)',
        'code': '663',
        'region': '029'
    },
    'MAR': {
        'alpha2': 'MA',
        'alpha3': 'MAR',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:MA',
        'name': 'Morocco',
        'code': '504',
        'region': '015'
    },
    'MCO': {
        'alpha2': 'MC',
        'alpha3': 'MCO',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:MC',
        'name': 'Monaco',
        'code': '492',
        'region': '155'
    },
    'MDA': {
        'alpha2': 'MD',
        'alpha3': 'MDA',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:MD',
        'name': 'Moldova',
        'code': '498',
        'region': '151'
    },
    'MDG': {
        'alpha2': 'MG',
        'alpha3': 'MDG',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:MG',
        'name': 'Madagascar',
        'code': '450',
        'region': '014'
    },
    'MDV': {
        'alpha2': 'MV',
        'alpha3': 'MDV',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:MV',
        'name': 'Maldives',
        'code': '462',
        'region': '034'
    },
    'MEX': {
        'alpha2': 'MX',
        'alpha3': 'MEX',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:MX',
        'name': 'Mexico',
        'code': '484',
        'region': '013'
    },
    'MHL': {
        'alpha2': 'MH',
        'alpha3': 'MHL',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:MH',
        'name': 'Marshall Islands',
        'code': '584',
        'region': '057'
    },
    'MKD': {
        'alpha2': 'MK',
        'alpha3': 'MKD',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:MK',
        'name': 'North Macedonia',
        'code': '807',
        'region': '039'
    },
    'MLI': {
        'alpha2': 'ML',
        'alpha3': 'MLI',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:ML',
        'name': 'Mali',
        'code': '466',
        'region': '011'
    },
    'MLT': {
        'alpha2': 'MT',
        'alpha3': 'MLT',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:MT',
        'name': 'Malta',
        'code': '470',
        'region': '039'
    },
    'MMR': {
        'alpha2': 'MM',
        'alpha3': 'MMR',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:MM',
        'name': 'Myanmar',
        'code': '104',
        'region': '035'
    },
    'MNE': {
        'alpha2': 'ME',
        'alpha3': 'MNE',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:ME',
        'name': 'Montenegro',
        'code': '499',
        'region': '039'
    },
    'MNG': {
        'alpha2': 'MN',
        'alpha3': 'MNG',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:MN',
        'name': 'Mongolia',
        'code': '496',
        'region': '030'
    },
    'MNP': {
        'alpha2': 'MP',
        'alpha3': 'MNP',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:MP',
        'name': 'Northern Mariana Islands',
        'code': '580',
        'region': '057'
    },
    'MOZ': {
        'alpha2': 'MZ',
        'alpha3': 'MOZ',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:MZ',
        'name': 'Mozambique',
        'code': '508',
        'region': '014'
    },
    'MRT': {
        'alpha2': 'MR',
        'alpha3': 'MRT',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:MR',
        'name': 'Mauritania',
        'code': '478',
        'region': '011'
    },
    'MSR': {
        'alpha2': 'MS',
        'alpha3': 'MSR',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:MS',
        'name': 'Montserrat',
        'code': '500',
        'region': '029'
    },
    'MTQ': {
        'alpha2': 'MQ',
        'alpha3': 'MTQ',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:MQ',
        'name': 'Martinique',
        'code': '474',
        'region': '029'
    },
    'MUS': {
        'alpha2': 'MU',
        'alpha3': 'MUS',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:MU',
        'name': 'Mauritius',
        'code': '480',
        'region': '014'
    },
    'MWI': {
        'alpha2': 'MW',
        'alpha3': 'MWI',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:MW',
        'name': 'Malawi',
        'code': '454',
        'region': '014'
    },
    'MYS': {
        'alpha2': 'MY',
        'alpha3': 'MYS',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:MY',
        'name': 'Malaysia',
        'code': '458',
        'region': '035'
    },
    'MYT': {
        'alpha2': 'YT',
        'alpha3': 'MYT',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:YT',
        'name': 'Mayotte',
        'code': '175',
        'region': '014'
    },
    'NAM': {
        'alpha2': 'NA',
        'alpha3': 'NAM',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:NA',
        'name': 'Namibia',
        'code': '516',
        'region': '018'
    },
    'NCL': {
        'alpha2': 'NC',
        'alpha3': 'NCL',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:NC',
        'name': 'New Caledonia',
        'code': '540',
        'region': '054'
    },
    'NER': {
        'alpha2': 'NE',
        'alpha3': 'NER',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:NE',
        'name': 'Niger',
        'code': '562',
        'region': '011'
    },
    'NFK': {
        'alpha2': 'NF',
        'alpha3': 'NFK',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:NF',
        'name': 'Norfolk Island',
        'code': '574',
        'region': '053'
    },
    'NGA': {
        'alpha2': 'NG',
        'alpha3': 'NGA',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:NG',
        'name': 'Nigeria',
        'code': '566',
        'region': '011'
    },
    'NIC': {
        'alpha2': 'NI',
        'alpha3': 'NIC',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:NI',
        'name': 'Nicaragua',
        'code': '558',
        'region': '013'
    },
    'NIU': {
        'alpha2': 'NU',
        'alpha3': 'NIU',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:NU',
        'name': 'Niue',
        'code': '570',
        'region': '061'
    },
    'NLD': {
        'alpha2': 'NL',
        'alpha3': 'NLD',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:NL',
        'name': 'Netherlands',
        'code': '528',
        'region': '155'
    },
    'NOR': {
        'alpha2': 'NO',
        'alpha3': 'NOR',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:NO',
        'name': 'Norway',
        'code': '578',
        'region': '154'
    },
    'NPL': {
        'alpha2': 'NP',
        'alpha3': 'NPL',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:NP',
        'name': 'Nepal',
        'code': '524',
        'region': '034'
    },
    'NRU': {
        'alpha2': 'NR',
        'alpha3': 'NRU',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:NR',
        'name': 'Nauru',
        'code': '520',
        'region': '057'
    },
    'NZL': {
        'alpha2': 'NZ',
        'alpha3': 'NZL',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:NZ',
        'name': 'New Zealand',
        'code': '554',
        'region': '053'
    },
    'OMN': {
        'alpha2': 'OM',
        'alpha3': 'OMN',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:OM',
        'name': 'Oman',
        'code': '512',
        'region': '145'
    },
    'PAK': {
        'alpha2': 'PK',
        'alpha3': 'PAK',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:PK',
        'name': 'Pakistan',
        'code': '586',
        'region': '034'
    },
    'PAN': {
        'alpha2': 'PA',
        'alpha3': 'PAN',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:PA',
        'name': 'Panama',
        'code': '591',
        'region': '013'
    },
    'PCN': {
        'alpha2': 'PN',
        'alpha3': 'PCN',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:PN',
        'name': 'Pitcairn',
        'code': '612',
        'region': '061'
    },
    'PER': {
        'alpha2': 'PE',
        'alpha3': 'PER',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:PE',
        'name': 'Peru',
        'code': '604',
        'region': '005'
    },
    'PHL': {
        'alpha2': 'PH',
        'alpha3': 'PHL',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:PH',
        'name': 'Philippines',
        'code': '608',
        'region': '035'
    },
    'PLW': {
        'alpha2': 'PW',
        'alpha3': 'PLW',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:PW',
        'name': 'Palau',
        'code': '585',
        'region': '057'
    },
    'PNG': {
        'alpha2': 'PG',
        'alpha3': 'PNG',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:PG',
        'name': 'Papua New Guinea',
        'code': '598',
        'region': '054'
    },
    'POL': {
        'alpha2': 'PL',
        'alpha3': 'POL',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:PL',
        'name': 'Poland',
        'code': '616',
        'region': '151'
    },
    'PRI': {
        'alpha2': 'PR',
        'alpha3': 'PRI',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:PR',
        'name': 'Puerto Rico',
        'code': '630',
        'region': '029'
    },
    'PRK': {
        'alpha2': 'KP',
        'alpha3': 'PRK',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:KP',
        'name': 'North Korea',
        'code': '408',
        'region': '030'
    },
    'PRT': {
        'alpha2': 'PT',
        'alpha3': 'PRT',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:PT',
        'name': 'Portugal',
        'code': '620',
        'region': '039'
    },
    'PRY': {
        'alpha2': 'PY',
        'alpha3': 'PRY',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:PY',
        'name': 'Paraguay',
        'code': '600',
        'region': '005'
    },
    'PSE': {
        'alpha2': 'PS',
        'alpha3': 'PSE',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:PS',
        'name': 'Palestine,  State of',
        'code': '275',
        'region': '145'
    },
    'PYF': {
        'alpha2': 'PF',
        'alpha3': 'PYF',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:PF',
        'name': 'French Polynesia',
        'code': '258',
        'region': '061'
    },
    'QAT': {
        'alpha2': 'QA',
        'alpha3': 'QAT',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:QA',
        'name': 'Qatar',
        'code': '634',
        'region': '145'
    },
    'REU': {
        'alpha2': 'RE',
        'alpha3': 'REU',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:RE',
        'name': 'Réunion',
        'code': '638',
        'region': '014'
    },
    'ROU': {
        'alpha2': 'RO',
        'alpha3': 'ROU',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:RO',
        'name': 'Romania',
        'code': '642',
        'region': '151'
    },
    'RUS': {
        'alpha2': 'RU',
        'alpha3': 'RUS',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:RU',
        'name': 'Russia',
        'code': '643',
        'region': '151'
    },
    'RWA': {
        'alpha2': 'RW',
        'alpha3': 'RWA',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:RW',
        'name': 'Rwanda',
        'code': '646',
        'region': '014'
    },
    'SAU': {
        'alpha2': 'SA',
        'alpha3': 'SAU',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:SA',
        'name': 'Saudi Arabia',
        'code': '682',
        'region': '145'
    },
    'SDN': {
        'alpha2': 'SD',
        'alpha3': 'SDN',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:SD',
        'name': 'Sudan',
        'code': '729',
        'region': '015'
    },
    'SEN': {
        'alpha2': 'SN',
        'alpha3': 'SEN',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:SN',
        'name': 'Senegal',
        'code': '686',
        'region': '011'
    },
    'SGP': {
        'alpha2': 'SG',
        'alpha3': 'SGP',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:SG',
        'name': 'Singapore',
        'code': '702',
        'region': '035'
    },
    'SGS': {
        'alpha2': 'GS',
        'alpha3': 'SGS',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:GS',
        'name': 'South Georgia and the South Sandwich Islands',
        'code': '239',
        'region': None
    },
    'SHN': {
        'alpha2': 'SH',
        'alpha3': 'SHN',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:SH',
        'name': 'Saint Helena,  Ascension and Tristan da Cunha',
        'code': '654',
        'region': '011'
    },
    'SJM': {
        'alpha2': 'SJ',
        'alpha3': 'SJM',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:SJ',
        'name': 'Svalbard and Jan Mayen',
        'code': '744',
        'region': '154'
    },
    'SLB': {
        'alpha2': 'SB',
        'alpha3': 'SLB',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:SB',
        'name': 'Solomon Islands',
        'code': '090',
        'region': '054'
    },
    'SLE': {
        'alpha2': 'SL',
        'alpha3': 'SLE',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:SL',
        'name': 'Sierra Leone',
        'code': '694',
        'region': '011'
    },
    'SLV': {
        'alpha2': 'SV',
        'alpha3': 'SLV',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:SV',
        'name': 'El Salvador',
        'code': '222',
        'region': '013'
    },
    'SMR': {
        'alpha2': 'SM',
        'alpha3': 'SMR',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:SM',
        'name': 'San Marino',
        'code': '674',
        'region': '039'
    },
    'SOM': {
        'alpha2': 'SO',
        'alpha3': 'SOM',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:SO',
        'name': 'Somalia',
        'code': '706',
        'region': '014'
    },
    'SPM': {
        'alpha2': 'PM',
        'alpha3': 'SPM',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:PM',
        'name': 'Saint Pierre and Miquelon',
        'code': '666',
        'region': '021'
    },
    'SRB': {
        'alpha2': 'RS',
        'alpha3': 'SRB',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:RS',
        'name': 'Serbia',
        'code': '688',
        'region': '039'
    },
    'SSD': {
        'alpha2': 'SS',
        'alpha3': 'SSD',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:SS',
        'name': 'South Sudan',
        'code': '728',
        'region': '015'
    },
    'STP': {
        'alpha2': 'ST',
        'alpha3': 'STP',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:ST',
        'name': 'Sao Tome and Principe',
        'code': '678',
        'region': '017'
    },
    'SUR': {
        'alpha2': 'SR',
        'alpha3': 'SUR',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:SR',
        'name': 'Suriname',
        'code': '740',
        'region': '005'
    },
    'SVK': {
        'alpha2': 'SK',
        'alpha3': 'SVK',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:SK',
        'name': 'Slovakia',
        'code': '703',
        'region': '151'
    },
    'SVN': {
        'alpha2': 'SI',
        'alpha3': 'SVN',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:SI',
        'name': 'Slovenia',
        'code': '705',
        'region': '039'
    },
    'SWE': {
        'alpha2': 'SE',
        'alpha3': 'SWE',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:SE',
        'name': 'Sweden',
        'code': '752',
        'region': '154'
    },
    'SWZ': {
        'alpha2': 'SZ',
        'alpha3': 'SWZ',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:SZ',
        'name': 'Eswatini',
        'code': '748',
        'region': '018'
    },
    'SXM': {
        'alpha2': 'SX',
        'alpha3': 'SXM',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:SX',
        'name': 'Sint Maarten (Dutch)',
        'code': '534',
        'region': "029"
    },
    'SYC': {
        'alpha2': 'SC',
        'alpha3': 'SYC',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:SC',
        'name': 'Seychelles',
        'code': '690',
        'region': '014'
    },
    'SYR': {
        'alpha2': 'SY',
        'alpha3': 'SYR',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:SY',
        'name': 'Syrian Arab Republic',
        'code': '760',
        'region': '145'
    },
    'TCA': {
        'alpha2': 'TC',
        'alpha3': 'TCA',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:TC',
        'name': 'Turks and Caicos Islands',
        'code': '796',
        'region': '029'
    },
    'TCD': {
        'alpha2': 'TD',
        'alpha3': 'TCD',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:TD',
        'name': 'Chad',
        'code': '148',
        'region': '017'
    },
    'TGO': {
        'alpha2': 'TG',
        'alpha3': 'TGO',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:TG',
        'name': 'Togo',
        'code': '768',
        'region': '011'
    },
    'THA': {
        'alpha2': 'TH',
        'alpha3': 'THA',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:TH',
        'name': 'Thailand',
        'code': '764',
        'region': '035'
    },
    'TJK': {
        'alpha2': 'TJ',
        'alpha3': 'TJK',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:TJ',
        'name': 'Tajikistan',
        'code': '762',
        'region': '143'
    },
    'TKL': {
        'alpha2': 'TK',
        'alpha3': 'TKL',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:TK',
        'name': 'Tokelau',
        'code': '772',
        'region': '061'
    },
    'TKM': {
        'alpha2': 'TM',
        'alpha3': 'TKM',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:TM',
        'name': 'Turkmenistan',
        'code': '795',
        'region': '143'
    },
    'TLS': {
        'alpha2': 'TL',
        'alpha3': 'TLS',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:TL',
        'name': 'Timor-Leste',
        'code': '626',
        'region': '035'
    },
    'TON': {
        'alpha2': 'TO',
        'alpha3': 'TON',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:TO',
        'name': 'Tonga',
        'code': '776',
        'region': '061'
    },
    'TTO': {
        'alpha2': 'TT',
        'alpha3': 'TTO',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:TT',
        'name': 'Trinidad and Tobago',
        'code': '780',
        'region': '029'
    },
    'TUN': {
        'alpha2': 'TN',
        'alpha3': 'TUN',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:TN',
        'name': 'Tunisia',
        'code': '788',
        'region': '015'
    },
    'TUR': {
        'alpha2': 'TR',
        'alpha3': 'TUR',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:TR',
        'name': 'Türkiye',
        'code': '792',
        'region': '145'
    },
    'TUV': {
        'alpha2': 'TV',
        'alpha3': 'TUV',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:TV',
        'name': 'Tuvalu',
        'code': '798',
        'region': '061'
    },
    'TWN': {
        'alpha2': 'TW',
        'alpha3': 'TWN',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:TW',
        'name': 'Taiwan',
        'code': '158',
        'region': '030'
    },
    'TZA': {
        'alpha2': 'TZ',
        'alpha3': 'TZA',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:TZ',
        'name': 'Tanzania',
        'code': '834',
        'region': '014'
    },
    'UGA': {
        'alpha2': 'UG',
        'alpha3': 'UGA',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:UG',
        'name': 'Uganda',
        'code': '800',
        'region': '014'
    },
    'UKR': {
        'alpha2': 'UA',
        'alpha3': 'UKR',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:UA',
        'name': 'Ukraine',
        'code': '804',
        'region': '151'
    },
    'UMI': {
        'alpha2': 'UM',
        'alpha3': 'UMI',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:UM',
        'name': 'United States Minor Outlying Islands',
        'code': '581',
        'region': None
    },
    'URY': {
        'alpha2': 'UY',
        'alpha3': 'URY',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:UY',
        'name': 'Uruguay',
        'code': '858',
        'region': '005'
    },
    'USA': {
        'alpha2': 'US',
        'alpha3': 'USA',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:US',
        'name': 'United States of America',
        'code': '840',
        'region': '021'
    },
    'UZB': {
        'alpha2': 'UZ',
        'alpha3': 'UZB',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:UZ',
        'name': 'Uzbekistan',
        'code': '860',
        'region': '143'
    },
    'VAT': {
        'alpha2': 'VA',
        'alpha3': 'VAT',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:VA',
        'name': 'Holy See',
        'code': '336',
        'region': '039'
    },
    'VCT': {
        'alpha2': 'VC',
        'alpha3': 'VCT',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:VC',
        'name': 'Saint Vincent and the Grenadines',
        'code': '670',
        'region': '029'
    },
    'VEN': {
        'alpha2': 'VE',
        'alpha3': 'VEN',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:VE',
        'name': 'Venezuela',
        'code': '862',
        'region': '005'
    },
    'VGB': {
        'alpha2': 'VG',
        'alpha3': 'VGB',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:VG',
        'name': 'Virgin Islands (British)',
        'code': '092',
        'region': '029'
    },
    'VIR': {
        'alpha2': 'VI',
        'alpha3': 'VIR',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:VI',
        'name': 'Virgin Islands (U.S.)',
        'code': '850',
        'region': '029'
    },
    'VNM': {
        'alpha2': 'VN',
        'alpha3': 'VNM',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:VN',
        'name': 'Vietnam',
        'code': '704',
        'region': '035'
    },
    'VUT': {
        'alpha2': 'VU',
        'alpha3': 'VUT',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:VU',
        'name': 'Vanuatu',
        'code': '548',
        'region': '054'
    },
    'WLF': {
        'alpha2': 'WF',
        'alpha3': 'WLF',
        'independent': False,
        'iso_3116_2': 'ISO 3166-2:WF',
        'name': 'Wallis and Futuna',
        'code': '876',
        'region': '061'
    },
    'WSM': {
        'alpha2': 'WS',
        'alpha3': 'WSM',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:WS',
        'name': 'Samoa',
        'code': '882',
        'region': '061'
    },
    'YEM': {
        'alpha2': 'YE',
        'alpha3': 'YEM',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:YE',
        'name': 'Yemen',
        'code': '887',
        'region': '145'
    },
    'ZAF': {
        'alpha2': 'ZA',
        'alpha3': 'ZAF',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:ZA',
        'name': 'South Africa',
        'code': '710',
        'region': '018'
    },
    'ZMB': {
        'alpha2': 'ZM',
        'alpha3': 'ZMB',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:ZM',
        'name': 'Zambia',
        'code': '894',
        'region': '014'
    },
    'ZWE': {
        'alpha2': 'ZW',
        'alpha3': 'ZWE',
        'independent': True,
        'iso_3116_2': 'ISO 3166-2:ZW',
        'name': 'Zimbabwe',
        'code': '716',
        'region': '014'
    }
}
