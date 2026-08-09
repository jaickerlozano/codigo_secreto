from drf_spectacular.generators import SchemaGenerator


def test_order_access_schema_describes_header_only_no_content_exchange():
    schema = SchemaGenerator().get_schema(request=None, public=True)
    lookup = schema['paths']['/api/orders/by-order-number/{order_number}/']
    exchange = schema['paths']['/api/orders/by-order-number/{order_number}/access/']['post']
    guest_access = schema['components']['schemas']['Order']['properties']['guest_access']

    assert [parameter['in'] for parameter in lookup['get']['parameters']] == ['path']
    assert guest_access['allOf'] == [{'$ref': '#/components/schemas/GuestAccess'}]
    assert guest_access['readOnly'] is True
    assert guest_access['nullable'] is True
    assert schema['components']['schemas']['GuestAccess']['properties'] == {
        'token': {'type': 'string'},
        'expires_at': {'type': 'string', 'format': 'date-time'},
    }
    assert schema['components']['schemas']['GuestAccess']['required'] == ['expires_at', 'token']
    assert 'requestBody' not in exchange
    assert {parameter['in'] for parameter in exchange['parameters']} == {'path', 'header'}
    assert next(
        parameter for parameter in exchange['parameters']
        if parameter['in'] == 'header'
    ) == {
        'in': 'header',
        'name': 'X-Order-Capability',
        'required': True,
        'schema': {'type': 'string'},
    }
    assert exchange['responses']['204'] == {'description': 'No response body'}


def test_order_creation_schema_uses_typed_guest_items_request():
    schema = SchemaGenerator().get_schema(request=None, public=True)
    request_ref = schema['paths']['/api/orders/']['post']['requestBody']['content'][
        'application/json'
    ]['schema']['$ref']

    assert request_ref == '#/components/schemas/OrderCreate'
    guest_items = schema['components']['schemas']['OrderCreate']['properties']['guest_items']
    assert guest_items['type'] == 'array'
    assert guest_items['items'] == {'$ref': '#/components/schemas/GuestOrderItem'}
    assert guest_items['writeOnly'] is True
    assert schema['components']['schemas']['GuestOrderItem']['properties'] == {
        'product_id': {'type': 'integer', 'minimum': 1},
        'quantity': {'type': 'integer', 'minimum': 1},
    }
