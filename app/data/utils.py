import datetime

from sqlalchemy import desc

from app import flask_app, log, data, db
from app.data import models as mmodels


def datetime_to_dutch_datetime_string(date, include_seconds=False):
    return mmodels.datetime_to_dutch_datetime_string(date, include_seconds=include_seconds)


def raise_error(message, details=None):
    error = Exception(f'm({message}), d({details}), td({type(details).__name__})')
    raise error


# standardized way to make a key from strings: sort alphabetically and concatenate
def make_key(item_list):
    return make_list(item_list, seperator=',')

def extend_key(item1, item2=None):
    if isinstance(item1, list):
        return ','.join(item1)
    return ','.join([item1, item2])


# standardized way to concatenate strings: sort alphabetically and concatenate; seperated by comma
def make_list(item_list, seperator=', '):
    return seperator.join(sorted(item_list))


belgische_gemeenten = [
	"ANDERLECHT",
	"OUDERGEM",
	"SINT-AGATHA-BERCHEM",
	"BRUSSEL",
	"ETTERBEEK",
	"EVERE",
	"VORST",
	"GANSHOREN",
	"ELSENE",
	"JETTE",
	"KOEKELBERG",
	"SINT-JANS-MOLENBEEK",
	"SINT-GILLIS",
	"SINT-JOOST-TEN-NODE",
	"SCHAARBEEK",
	"UKKEL",
	"WATERMAAL-BOSVOORDE",
	"SINT-LAMBRECHTS-WOLUWE",
	"SINT-PIETERS-WOLUWE",
	"AARTSELAAR",
	"ANTWERPEN",
	"BOECHOUT",
	"BOOM",
	"BORSBEEK",
	"BRASSCHAAT",
	"BRECHT",
	"EDEGEM",
	"ESSEN",
	"HEMIKSEM",
	"HOVE",
	"KALMTHOUT",
	"KAPELLEN",
	"KONTICH",
	"LINT",
	"MALLE",
	"MORTSEL",
	"NIEL",
	"RANST",
	"RUMST",
	"SCHELLE",
	"SCHILDE",
	"SCHOTEN",
	"STABROEK",
	"WIJNEGEM",
	"WOMMELGEM",
	"WUUSTWEZEL",
	"ZANDHOVEN",
	"ZOERSEL",
	"ZWIJNDRECHT",
	"BERLAAR",
	"BONHEIDEN",
	"BORNEM",
	"DUFFEL",
	"HEIST-OP-DEN-BERG",
	"LIER",
	"MECHELEN",
	"NIJLEN",
	"PUTTE",
	"PUURS-SINT-AMANDS",
	"SINT-KATELIJNE-WAVER",
	"WILLEBROEK",
	"ARENDONK",
	"BAARLE-HERTOG",
	"BALEN",
	"BEERSE",
	"DESSEL",
	"GEEL",
	"GROBBENDONK",
	"HERENTALS",
	"HERENTHOUT",
	"HERSELT",
	"HOOGSTRATEN",
	"HULSHOUT",
	"KASTERLEE",
	"LAAKDAL",
	"LILLE",
	"MEERHOUT",
	"MERKSPLAS",
	"MOL",
	"OLEN",
	"OUD-TURNHOUT",
	"RAVELS",
	"RETIE",
	"RIJKEVORSEL",
	"TURNHOUT",
	"VORSELAAR",
	"VOSSELAAR",
	"WESTERLO",
	"AFFLIGEM",
	"ASSE",
	"BEERSEL",
	"BEVER",
	"DILBEEK",
	"DROGENBOS",
	"GALMAARDEN",
	"GOOIK",
	"GRIMBERGEN",
	"HALLE",
	"HERNE",
	"HOEILAART",
	"KAMPENHOUT",
	"KAPELLE-OP-DEN-BOS",
	"KRAAINEM",
	"LENNIK",
	"LIEDEKERKE",
	"LINKEBEEK",
	"LONDERZEEL",
	"MACHELEN",
	"MEISE",
	"MERCHTEM",
	"OPWIJK",
	"OVERIJSE",
	"PEPINGEN",
	"SINT-GENESIUS-RODE",
	"ROOSDAAL",
	"SINT-PIETERS-LEEUW",
	"STEENOKKERZEEL",
	"TERNAT",
	"VILVOORDE",
	"WEMMEL",
	"WEZEMBEEK-OPPEM",
	"ZAVENTEM",
	"ZEMST",
	"AARSCHOT",
	"BEGIJNENDIJK",
	"BEKKEVOORT",
	"BERTEM",
	"BIERBEEK",
	"BOORTMEERBEEK",
	"BOUTERSEM",
	"DIEST",
	"GEETBETS",
	"GLABBEEK",
	"HAACHT",
	"HERENT",
	"HOEGAARDEN",
	"HOLSBEEK",
	"HULDENBERG",
	"KEERBERGEN",
	"KORTENAKEN",
	"KORTENBERG",
	"LANDEN",
	"ZOUTLEEUW",
	"LINTER",
	"LEUVEN",
	"LUBBEEK",
	"SCHERPENHEUVEL-ZICHEM",
	"OUD-HEVERLEE",
	"ROTSELAAR",
	"TERVUREN",
	"TIELT-WINGE",
	"TIENEN",
	"TREMELO",
	"BEERNEM",
	"BLANKENBERGE",
	"BRUGGE",
	"DAMME",
	"JABBEKE",
	"KNOKKE-HEIST",
	"OOSTKAMP",
	"TORHOUT",
	"ZEDELGEM",
	"ZUIENKERKE",
	"ANZEGEM",
	"AVELGEM",
	"KORTRIJK",
	"DEERLIJK",
	"SPIERE-HELKIJN",
	"HARELBEKE",
	"KUURNE",
	"LENDELEDE",
	"MENEN",
	"WAREGEM",
	"WEVELGEM",
	"ZWEVEGEM",
	"DIKSMUIDE",
	"HOUTHULST",
	"KOEKELARE",
	"KORTEMARK",
	"LO-RENINGE",
	"ALVERINGEM",
	"VEURNE",
	"KOKSIJDE",
	"DE PANNE",
	"NIEUWPOORT",
	"BREDENE",
	"DE HAAN",
	"GISTEL",
	"ICHTEGEM",
	"MIDDELKERKE",
	"OOSTENDE",
	"OUDENBURG",
	"HOOGLEDE",
	"INGELMUNSTER",
	"IZEGEM",
	"LEDEGEM",
	"LICHTERVELDE",
	"MOORSLEDE",
	"ROESELARE",
	"STADEN",
	"ARDOOIE",
	"DENTERGEM",
	"MEULEBEKE",
	"OOSTROZEBEKE",
	"PITTEM",
	"RUISELEDE",
	"TIELT",
	"WIELSBEKE",
	"WINGENE",
	"HEUVELLAND",
	"LANGEMARK-POELKAPELLE",
	"MESEN",
	"POPERINGE",
	"VLETEREN",
	"WERVIK",
	"IEPER",
	"ZONNEBEKE",
	"AALST",
	"DENDERLEEUW",
	"ERPE-MERE",
	"GERAARDSBERGEN",
	"HAALTERT",
	"HERZELE",
	"LEDE",
	"NINOVE",
	"SINT-LIEVENS-HOUTEM",
	"ZOTTEGEM",
	"OUDENAARDE",
	"BRAKEL",
	"HOREBEKE",
	"KLUISBERGEN",
	"KRUISEM",
	"LIERDE",
	"MAARKEDAL",
	"RONSE",
	"WORTEGEM-PETEGEM",
	"ZWALM",
	"ASSENEDE",
	"EEKLO",
	"KAPRIJKE",
	"MALDEGEM",
	"SINT-LAUREINS",
	"ZELZATE",
	"AALTER",
	"DE PINTE",
	"DEINZE",
	"DESTELBERGEN",
	"EVERGEM",
	"GENT",
	"GAVERE",
	"LIEVEGEM",
	"LOCHRISTI",
	"MELLE",
	"MERELBEKE",
	"MOERBEKE",
	"NAZARETH",
	"OOSTERZELE",
	"SINT-MARTENS-LATEM",
	"WACHTEBEKE",
	"ZULTE",
	"BEVEREN",
	"KRUIBEKE",
	"LOKEREN",
	"SINT-NIKLAAS",
	"SINT-GILLIS-WAAS",
	"STEKENE",
	"TEMSE",
	"BERLARE",
	"BUGGENHOUT",
	"HAMME",
	"LAARNE",
	"LEBBEKE",
	"DENDERMONDE",
	"WAASMUNSTER",
	"WETTEREN",
	"WICHELEN",
	"ZELE",
	"AS",
	"BERINGEN",
	"LEOPOLDSBURG",
	"DIEPENBEEK",
	"GENK",
	"GINGELOM",
	"HALEN",
	"HAM",
	"HASSELT",
	"HERK-DE-STAD",
	"HEUSDEN-ZOLDER",
	"LUMMEN",
	"NIEUWERKERKEN",
	"SINT-TRUIDEN",
	"TESSENDERLO",
	"ZONHOVEN",
	"ZUTENDAAL",
	"BOCHOLT",
	"BREE",
	"DILSEN-STOKKEM",
	"HAMONT-ACHEL",
	"HECHTEL-EKSEL",
	"HOUTHALEN-HELCHTEREN",
	"KINROOI",
	"LOMMEL",
	"MAASEIK",
	"OUDSBERGEN",
	"PEER",
	"PELT",
	"ALKEN",
	"BILZEN",
	"VOEREN",
	"HEERS",
	"HERSTAPPE",
	"HOESELT",
	"KORTESSEM",
	"LANAKEN",
	"BORGLOON",
	"MAASMECHELEN",
	"RIEMST",
	"TONGEREN",
	"WELLEN",
	"BEVEKOM",
	"EIGENBRAKEL",
	"KASTEELBRAKEL",
	"CHASTRE",
	"CHAUMONT-GISTOUX",
	"COURT-SAINT-ETIENNE",
	"GENEPIEN",
	"GRAVEN",
	"HÉLÉCINE",
	"INCOURT",
	"ITTER",
	"GELDENAKEN",
	"TERHULPEN",
	"LASNE",
	"MONT-SAINT-GUIBERT",
	"NIJVEL",
	"ORP-JAUCHE",
	"OTTIGNIES-LOUVAIN-LA-NEUVE",
	"PERWIJS",
	"RAMILLIES",
	"REBECQ",
	"RIXENSART",
	"TUBEKE",
	"VILLERS-LA-VILLE",
	"WALHAIN",
	"WATERLOO",
	"WAVER",
	"AAT",
	"BELOEIL",
	"BERNISSART",
	"BRUGELETTE",
	"CHIÈVRES",
	"ELZELE",
	"EDINGEN",
	"VLOESBERG",
	"FRASNES-LEZ-ANVAING",
	"LESSEN",
	"OPZULLIK",
	"AISEAU-PRESLES",
	"CHAPELLE-LEZ-HERLAIMONT",
	"CHARLEROI",
	"CHÂTELET",
	"COURCELLES",
	"FARCIENNES",
	"FLEURUS",
	"FONTAINE-L'EVÊQUE",
	"GERPINNES",
	"LES BONS VILLERS",
	"MONTIGNY-LE-TILLEUL",
	"PONT-À-CELLES",
	"BOUSSU",
	"COLFONTAINE",
	"DOUR",
	"FRAMERIES",
	"HENSIES",
	"HONNELLES",
	"JURBEKE",
	"LENS",
	"BERGEN",
	"QUAREGNON",
	"QUÉVY",
	"QUIÉVRAIN",
	"SAINT-GHISLAIN",
	"'S GRAVENBRAKEL",
	"ECAUSSINNES",
	"LE ROEULX",
	"MANAGE",
	"SENEFFE",
	"ZINNIK",
	"ANDERLUES",
	"BEAUMONT",
	"CHIMAY",
	"ERQUELINNES",
	"FROIDCHAPELLE",
	"HAM-SUR-HEURE-NALINNES",
	"LOBBES",
	"MERBES-LE-CHÂTEAU",
	"MOMIGNIES",
	"SIVRY-RANCE",
	"THUIN",
	"ANTOING",
	"BRUNEHAUT",
	"CELLES",
	"KOMEN-WAASTEN",
	"ESTAIMPUIS",
	"LEUZE-EN-HAINAUT",
	"MONT-DE-L'ENCLUS",
	"MOESKROEN",
	"PECQ",
	"PÉRUWELZ",
	"RUMES",
	"DOORNIK",
	"LA LOUVIÈRE",
	"BINCHE",
	"ESTINNES",
	"MORLANWELZ",
	"AMAY",
	"ANTHISNES",
	"BURDINNE",
	"CLAVIER",
	"ENGIS",
	"FERRIÈRES",
	"HAMOIR",
	"HÉRON",
	"HOEI",
	"MARCHIN",
	"MODAVE",
	"NANDRIN",
	"OUFFET",
	"TINLOT",
	"VERLAINE",
	"VILLERS-LE-BOUILLET",
	"WANZE",
	"ANS",
	"AWANS",
	"AYWAILLE",
	"BITSINGEN",
	"BEYNE-HEUSAY",
	"BLÉGNY",
	"CHAUDFONTAINE",
	"COMBLAIN-AU-PONT",
	"DALHEM",
	"ESNEUX",
	"FLÉMALLE",
	"FLÉRON",
	"GRÂCE-HOLLOGNE",
	"HERSTAL",
	"JUPRELLE",
	"LUIK",
	"NEUPRÉ",
	"OUPEYE",
	"SAINT-NICOLAS",
	"SERAING",
	"SOUMAGNE",
	"SPRIMONT",
	"TROOZ",
	"WEZET",
	"AMEL",
	"AUBEL",
	"BAELEN",
	"BÜLLINGEN",
	"BURG-REULAND",
	"BÜTGENBACH",
	"DISON",
	"EUPEN",
	"HERVE",
	"JALHAY",
	"KELMIS",
	"LIERNEUX",
	"LIMBURG",
	"LONTZEN",
	"MALMEDY",
	"OLNE",
	"PEPINSTER",
	"PLOMBIÈRES",
	"RAEREN",
	"SANKT VITH",
	"SPA",
	"STAVELOT",
	"STOUMONT",
	"THEUX",
	"THIMISTER-CLERMONT",
	"TROIS-PONTS",
	"VERVIERS",
	"WEISMES",
	"WELKENRAEDT",
	"BERLOZ",
	"BRAIVES",
	"CRISNÉE",
	"DONCEEL",
	"FAIMES",
	"FEXHE-LE-HAUT-CLOCHER",
	"GEER",
	"HANNUIT",
	"LIJSEM",
	"OERLE",
	"REMICOURT",
	"SAINT-GEORGES-SUR-MEUSE",
	"BORGWORM",
	"WASSEIGES",
	"AARLEN",
	"ATTERT",
	"AUBANGE",
	"MARTELANGE",
	"MESSANCY",
	"BASTENAKEN",
	"BERTOGNE",
	"FAUVILLERS",
	"GOUVY",
	"HOUFFALIZE",
	"SAINTE-ODE",
	"VAUX-SUR-SÛRE",
	"VIELSALM",
	"DURBUY",
	"EREZÉE",
	"HOTTON",
	"LA ROCHE-EN-ARDENNE",
	"MANHAY",
	"MARCHE-EN-FAMENNE",
	"NASSOGNE",
	"RENDEUX",
	"TENNEVILLE",
	"BERTRIX",
	"BOUILLON",
	"DAVERDISSE",
	"HERBEUMONT",
	"LÉGLISE",
	"LIBIN",
	"LIBRAMONT-CHEVIGNY",
	"NEUFCHÂTEAU",
	"PALISEUL",
	"SAINT-HUBERT",
	"TELLIN",
	"WELLIN",
	"CHINY",
	"ETALLE",
	"FLORENVILLE",
	"HABAY",
	"MEIX-DEVANT-VIRTON",
	"MUSSON",
	"ROUVROY",
	"SAINT-LÉGER",
	"TINTIGNY",
	"VIRTON",
	"ANHÉE",
	"BEAURAING",
	"BIÈVRE",
	"CINEY",
	"DINANT",
	"GEDINNE",
	"HAMOIS",
	"HASTIÈRE",
	"HAVELANGE",
	"HOUYET",
	"ONHAYE",
	"ROCHEFORT",
	"SOMME-LEUZE",
	"VRESSE-SUR-SEMOIS",
	"YVOIR",
	"ANDENNE",
	"ASSESSE",
	"EGHEZÉE",
	"FERNELMONT",
	"FLOREFFE",
	"FOSSES-LA-VILLE",
	"GEMBLOUX",
	"GESVES",
	"JEMEPPE-SUR-SAMBRE",
	"LA BRUYÈRE",
	"METTET",
	"NAMEN",
	"OHEY",
	"PROFONDEVILLE",
	"SAMBREVILLE",
	"SOMBREFFE",
	"CERFONTAINE",
	"COUVIN",
	"DOISCHE",
	"FLORENNES",
	"PHILIPPEVILLE",
	"VIROINVAL",
	"WALCOURT"
]
