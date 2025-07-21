import pyhocon

def test_hocon_file():
    try:
        config = pyhocon.ConfigFactory.parse_file("neuro_san/registries/legal_discovery_automation_system.hocon")
        print("HOCON file loaded successfully.")
        print("Tools:")
        for tool in config["toolbox"]["tools"]:
            print(f"  - {tool['name']}")
    except Exception as e:
        print(f"Error loading HOCON file: {e}")

if __name__ == "__main__":
    test_hocon_file()
