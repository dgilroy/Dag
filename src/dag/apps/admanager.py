import dag

admanager = dag.app("admanager", doc = "https://developers.google.com/ad-manager/api/start", help = "Utility tools for google ad manager")
VERSION = 'v202302'


def auth():
	from googleads import oauth2
	return oauth2.GoogleServiceAccountClient(dag.env.GOOGLE_ADS_KEY_LOCATION, oauth2.GetAPIScope('ad_manager'))

def get_client():
	from googleads import ad_manager
	oauth2_client = auth()
	# Initialize a client object, by default uses the credentials in ~/googleads.yaml.
	return ad_manager.AdManagerClient.LoadFromStorage()

def get_statement_builder(version = None):
	from googleads import ad_manager
	return ad_manager.StatementBuilder(version = version or VERSION)

def serialize(item):
	from zeep import helpers as zeep_helpers
	item = dict(zeep_helpers.serialize_object(item))

	for k,v in item.items():
		if isinstance(v, dict):
			item[k] = serialize(v)

	return item

def get_service(service, version = None):
	client = get_client()
	return client.GetService(service, version=version or VERSION)


@admanager.DEFAULT.collection
def orders():
	from googleads import ad_manager

	order_service = get_service('OrderService')
	statement = get_statement_builder()

	items = []
	while True:
		response = order_service.getOrdersByStatement(statement.ToStatement())
		if "results" in response and response.results:
			items.extend([serialize(r) for r in response.results])
			statement.offset += statement.limit
		else:
			break

	return items
orders.resources("order").ID("id").LABEL("name").LAUNCH("https://admanager.google.com/1160771#delivery/order/order_overview/order_id={id}")


@orders.op.collection
def lineitems(order):
	line_item_service = get_service('LineItemService')
	statement = get_statement_builder().Where(f"OrderId = {order.id}")

	items = []
	while True:
		response = line_item_service.getLineItemsByStatement(statement.ToStatement())
		if 'results' in response and len(response['results']):
			items.extend([serialize(r) for r in response.results])
			statement.offset += statement.limit
		else:
			break

	return items
lineitems.resources("lineitem").ID("id").LABEL("name").LAUNCH("https://admanager.google.com/1160771#delivery/line_item/detail/line_item_id={id}&order_id={orderId}&li_tab=settings&sort_by=StartDateTime&sort_asc=false")
