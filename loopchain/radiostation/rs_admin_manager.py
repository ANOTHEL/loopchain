# Copyright 2018 ICON Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""A management class for peer and channel list."""
from loopchain.baseservice import PeerManager
from loopchain.blockchain import *


class AdminManager:
    """Radiostation 내에서 Channel 정보와 Peer 정보를 관리한다."""

    def __init__(self, store_identity):

        key_value_store, key_value_store_path = util.init_default_key_value_store(f"{store_identity}_admin")
        self.__key_value_store = key_value_store
        self.__key_value_store_path = key_value_store_path

        self.__json_data = None
        self.load_json_data(conf.CHANNEL_MANAGE_DATA_PATH)

    def save_peer_manager(self, channel, peer_manager: PeerManager):
        """peer_list 를 key value store 에 저장한다.

        :param channel:
        :param peer_manager:
        """
        # util.logger.spam(f"rs_admin_manager:save_peer_manager")

        store_key = str.encode(conf.LEVEL_DB_KEY_FOR_PEER_LIST + f"_{channel}")

        try:
            dump = peer_manager.dump()
            self.__key_value_store.put(store_key, dump)
        except AttributeError as e:
            logging.warning("Fail Save Peer_list: " + str(e))

    def load_peer_manager(self, channel):
        """key value store 로 부터 peer_manager 를 가져온다.

        :return: peer_manager
        """
        store_key = str.encode(conf.LEVEL_DB_KEY_FOR_PEER_LIST + f"_{channel}")

        peer_manager = PeerManager(channel)

        try:
            peer_list_data = pickle.loads(self.__key_value_store.get(store_key))
            peer_manager.load(peer_list_data)
            logging.debug("load peer_list_data from db: " + peer_manager.get_peers_for_debug()[0])
        except KeyError:
            logging.warning("There is no peer_list_data in db")

        return peer_manager

    def load_json_data(self, channel_manage_data_path):
        """open channel_manage_data json file and load the data
        :param channel_manage_data_path:
        :return:
        """
        try:
            logging.debug(f"try to load channel management data from json file ({channel_manage_data_path})")
            with open(channel_manage_data_path) as file:
                json_data = json.load(file)
                json_string = json.dumps(json_data).replace('[local_ip]', util.get_private_ip())
                self.__json_data = json.loads(json_string)

                logging.info(f"loading channel info : {self.json_data}")
        except FileNotFoundError as e:
            util.exit_and_msg(f"cannot open json file in ({channel_manage_data_path}): {e}")

    @property
    def json_data(self) -> dict:
        return self.__json_data

    def get_channel_list(self) -> list:
        return list(self.json_data)

    def save_channel_manage_data(self, updated_data):
        with open(conf.CHANNEL_MANAGE_DATA_PATH, 'w') as f:
            json.dump(updated_data, f, indent=2)
        self.load_json_data(conf.CHANNEL_MANAGE_DATA_PATH)

    def get_all_channel_info(self) -> str:
        return json.dumps(self.json_data)

    def get_score_package(self, channel) -> str:
        return self.json_data[channel]["score_package"]

    def get_channel_infos_by_peer_target(self, peer_target: str) -> str:
        """get channel infos (channel, score_package, and peer target) that includes certain peer target

        :param peer_target:
        :return: channel_infos
        """
        filtered_channel = {}
        for channel in self.json_data:
            for each_target in self.json_data[channel]["peers"]:
                if peer_target == each_target["peer_target"]:
                    filtered_channel[channel] = self.json_data[channel]
        return json.dumps(filtered_channel)

    def get_peer_list_by_channel(self, channel: str) -> list:
        """get peer list by channel

        :param channel:
        :return:
        """
        peer_list = [each['peer_target'] for each in self.json_data[channel]["peers"]]
        return peer_list

    def add_channel(self, loaded_data, new_channel, score_package_input):
        loaded_data[new_channel] = {"score_package": score_package_input, "peers": []}
        logging.info(f"Added channel({new_channel}), Current multichannel configuration is: {loaded_data}")
        self.save_channel_manage_data(loaded_data)

    def add_peer_target(self, loaded_data, channel_list, new_peer_target, peer_target_list, i):
        if new_peer_target not in [dict_data['peer_target'] for dict_data in peer_target_list]:
            peer_target_list.append({'peer_target': new_peer_target})
            logging.debug(f"Added peer({new_peer_target}), Current multichannel configuration is: {loaded_data}")
        else:
            logging.warning(f"peer_target: {new_peer_target} is already in channel: {channel_list[i]}")
        return loaded_data

    def delete_channel(self, loaded_data, channel_list, i):
        logging.info(f"Deleted channel({channel_list[i]})")
        del loaded_data[channel_list[i]]
        logging.info(f"Current multichannel configuration is: {loaded_data}")
        return loaded_data

    def delete_peer_target(self, loaded_data, remove_peer_target, filtered_list, i):
        for peer_target in loaded_data[filtered_list[i]]["peers"]:
            if remove_peer_target in peer_target["peer_target"]:
                loaded_data[filtered_list[i]]["peers"].remove(peer_target)
                logging.debug(f"Deleted peer({remove_peer_target}), "
                              f"Current multichannel configuration is: {loaded_data}")
        return loaded_data
