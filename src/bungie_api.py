import requests
from urllib.parse import quote


class BungieApi:
    def __init__(self, api_key, access_token):
        self.api_key = api_key
        self.access_token = access_token

    def __default_headers(self):
        return {
            "X-API-Key": self.api_key,
        }

    def get_primary_membership_id_and_type(self, username):
        username = quote(username)
        url = f"https://www.bungie.net/Platform/Destiny2/SearchDestinyPlayer/-1/{username}/"
        response = requests.get(url, headers=self.__default_headers())
        data = response.json()

        for player in data["Response"]:
            membership_id = player["membershipId"]
            membership_type = player["membershipType"]
            print(
                f"Checking membership ID {membership_id} with membership type {membership_type}"
            )
            profile_url = f"https://www.bungie.net/Platform/Destiny2/{membership_type}/Profile/{membership_id}/?components=100"
            profile_response = requests.get(
                profile_url, headers=self.__default_headers()
            )
            profile_data = profile_response.json()
            if (
                "profile" in profile_data["Response"]
                and profile_data["Response"]["profile"]["data"]["userInfo"][
                    "crossSaveOverride"
                ]
                == membership_type
            ):
                print(f"Crosave override found for {membership_id}")
                return membership_id, membership_type

        return None

    def get_character_ids_and_classes(self, membership_id, membership_type):
        url = f"https://www.bungie.net/Platform/Destiny2/{membership_type}/Profile/{membership_id}/?components=200"
        response = requests.get(url, headers=self.__default_headers())
        data = response.json()

        character_data = data["Response"]["characters"]["data"]
        character_ids_and_classes = {}
        for character_id, character_info in character_data.items():
            class_type = character_info["classType"]
            if class_type == 0:
                class_name = "Titan"
            elif class_type == 1:
                class_name = "Hunter"
            elif class_type == 2:
                class_name = "Warlock"
            else:
                class_name = "Unknown"
            character_ids_and_classes[character_id] = class_name

        return character_ids_and_classes

    def get_manifest(self):
        url = "https://www.bungie.net/Platform/Destiny2/Manifest/"

        response = requests.get(url, headers=self.__default_headers())
        response.raise_for_status()

        manifest = response.json()

        return manifest

    def __get_item_definitions(self, manifest):
        item_definitions_url = f'https://www.bungie.net{manifest["Response"]["jsonWorldComponentContentPaths"]["en"]["DestinyInventoryItemDefinition"]}'

        response = requests.get(item_definitions_url, headers=self.__default_headers())
        response.raise_for_status()

        item_definitions = response.json()

        return item_definitions

    def __get_stat_definitions(self, manifest):
        stat_definitions_url = f'https://www.bungie.net{manifest["Response"]["jsonWorldComponentContentPaths"]["en"]["DestinyStatDefinition"]}'

        response = requests.get(stat_definitions_url, headers=self.__default_headers())
        response.raise_for_status()

        stat_definitions = response.json()

        return stat_definitions

    def get_static_definitions(self):
        manifest = self.get_manifest()
        item_definitions = self.__get_item_definitions(manifest)
        stat_definitions = self.__get_stat_definitions(manifest)
        return item_definitions, stat_definitions

    # full description of components are on the bungie API documentation: https://bungie-net.github.io/multi/schema_Destiny-DestinyComponentType.html
    def get_profile(self, access_token, membership_type, membership_id, components):
        headers = self.__default_headers()
        headers["Authorization"] = f"Bearer {access_token}"

        joined_components = ",".join(str(c) for c in components)

        url = f"https://www.bungie.net/Platform/Destiny2/{membership_type}/Profile/{membership_id}/?components={joined_components}"

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()["Response"]
        return data
