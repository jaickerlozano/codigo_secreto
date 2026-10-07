from pathlib import Path

import yaml
from drf_spectacular.generators import SchemaGenerator
from jsonschema import Draft7Validator

from apps.orders.models import Order
from apps.orders.serializers import OrderSerializer

_SCHEMA_FILE = Path(__file__).resolve().parents[3] / "schema.yaml"


def _committed_schema():
    return yaml.safe_load(_SCHEMA_FILE.read_text())


def test_order_cancellation_reason_schema_accepts_runtime_blank_and_known_reasons():
    field = OrderSerializer().fields['cancellation_reason']
    runtime_blank = field.to_representation(Order().cancellation_reason)
    assert runtime_blank == ''
    assert field.read_only is True

    for schema in (SchemaGenerator().get_schema(request=None, public=True), _committed_schema()):
        reason = schema['components']['schemas']['Order']['properties']['cancellation_reason']
        validator = Draft7Validator({**reason, 'components': schema['components']})
        assert reason['readOnly'] is True
        assert validator.is_valid(runtime_blank)
        for value in ('BUYER', 'ADMIN', 'EXPIRED'):
            assert validator.is_valid(value)
        for value in (None, 'UNKNOWN', 'buyer'):
            assert not validator.is_valid(value)
        assert reason['oneOf'] == [
            {'$ref': '#/components/schemas/CancellationReasonEnum'},
            {'$ref': '#/components/schemas/BlankEnum'},
        ]


def test_committed_schema_exposes_dispatch_options_contract():
    schema = _committed_schema()
    operation = schema["paths"]["/api/shipping/dispatch-options/"]["get"]

    comuna_param = next(
        parameter for parameter in operation["parameters"]
        if parameter["name"] == "comuna"
    )
    assert comuna_param["in"] == "query"
    assert comuna_param["required"] is True
    assert comuna_param["schema"] == {"type": "integer"}
    assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/DispatchOptions"
    }


def test_committed_schema_keeps_order_delivery_selection_but_hides_agreement():
    schema = _committed_schema()
    order = schema["components"]["schemas"]["Order"]["properties"]

    assert order["delivery_kind"] == {"$ref": "#/components/schemas/DeliveryKindEnum"}
    assert order["requested_dispatch_date"]["type"] == "string"
    assert order["requested_dispatch_date"]["nullable"] is True
    assert order["delivery_gate_status"]["type"] == "string"
    assert order["delivery_gate_status"]["readOnly"] is True
    assert order["shipping_option_id"]["type"] == "integer"
    assert order["shipping_option_id"]["writeOnly"] is True
    # Unit E removed the agreement-write field from the public read surface.
    assert "special_delivery_agreed_at" not in order


def test_committed_schema_accepts_delivery_selection_on_order_create():
    schema = _committed_schema()
    order_create = schema["components"]["schemas"]["OrderCreate"]["properties"]

    assert order_create["delivery_kind"] == {
        "$ref": "#/components/schemas/DeliveryKindEnum"
    }
    assert order_create["requested_dispatch_date"]["type"] == "string"
    assert order_create["requested_dispatch_date"]["format"] == "date"
    assert order_create["requested_dispatch_date"]["nullable"] is True
    assert order_create["shipping_option_id"]["type"] == "integer"
    assert order_create["shipping_option_id"]["writeOnly"] is True
    assert order_create["shipping_option_id"]["nullable"] is True


def test_committed_schema_documents_special_delivery_409_recovery_body():
    schema = _committed_schema()
    operation = schema["paths"]["/api/payments/initiate/"]["post"]

    error_ref = operation["responses"]["409"]["content"]["application/json"]["schema"][
        "$ref"
    ]
    assert error_ref == "#/components/schemas/SpecialDeliveryAgreementRequiredError"
    error = schema["components"]["schemas"]["SpecialDeliveryAgreementRequiredError"]
    assert error["required"] == ["code", "detail", "poll_after_seconds", "whatsapp_url"]
    assert error["properties"]["code"]["type"] == "string"
    assert error["properties"]["detail"]["type"] == "string"
    assert error["properties"]["whatsapp_url"]["type"] == "string"
    assert error["properties"]["whatsapp_url"]["format"] == "uri"
    assert error["properties"]["poll_after_seconds"]["type"] == "integer"
    assert error["properties"]["poll_after_seconds"]["minimum"] == 1


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
    confirmed_revision = schema['components']['schemas']['OrderCreate']['properties'][
        'confirmed_revision'
    ]
    assert confirmed_revision['type'] == 'string'
    assert confirmed_revision['writeOnly'] is True
    for contract in (schema, _committed_schema()):
        assert contract['paths']['/api/orders/checkout-context/']['post']['responses']['204'] == {'description': 'No response body'}
        pending = contract['paths']['/api/orders/pending/']['get']
        assert set(pending['responses']) == {'200', '204'}
        assert 'parameters' not in pending
        properties = contract['components']['schemas']['Order']['properties']
        assert properties['payment_expires_at'] == {'type': 'string', 'format': 'date-time', 'readOnly': True, 'nullable': True}
        assert properties['cancellation_reason']['readOnly'] is True
    assert schema['components']['schemas']['GuestOrderItem']['properties'] == {
        'product_id': {'type': 'integer', 'minimum': 1},
        'quantity': {'type': 'integer', 'minimum': 1},
    }
