from scripts.audit_phase7 import audit

def test_pages_and_local_runtime_work_with_network_forbidden():
    result=audit()
    assert len(result['pages'])==5
    assert result['physical_wifi_ethernet_disconnect']=='PENDING_USER_REHEARSAL'
    assert result['whole_app_wcag_conformance']=='NOT_ESTABLISHED'
