from backend.main import create_app

app = create_app()

with app.app_context():
    print("\n🔍 Registered Routes:")
    print("-" * 50)

    for rule in app.url_map.iter_rules():
        # Defensive check in case rule.methods is None (rare but possible)
        method_list = sorted(rule.methods) if rule.methods else []
        methods = ", ".join(method_list)
        print(f"[{methods:<20}] {rule.rule:<35} → {rule.endpoint}")
