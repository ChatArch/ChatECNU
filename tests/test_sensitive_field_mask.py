from chatecnu.config import ECNUConfig


def test_ecnu_password_fields_use_full_shared_masking(monkeypatch):
    canary = 'DUMMY_ECNU_LONG_PASSWORD_CANARY_123456789'
    for name in ['ECNU_PASSWORD', 'ECNU_VISITOR_PASSWORD1', 'ECNU_VISITOR_PASSWORD2']:
        field = getattr(ECNUConfig, name)
        assert field.is_sensitive is True
        monkeypatch.setattr(field, 'value', canary)
        assert field.mask_value() == '*' * len(canary)
