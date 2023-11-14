# coding=utf-8
# Copyright 2019-present, the HuggingFace Inc. team.
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

import importlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

import mindnlp.transformers.models.auto
from mindnlp.transformers.models.auto.configuration_auto import CONFIG_MAPPING, AutoConfig
from mindnlp.transformers.models.bert.configuration_bert import BertConfig
from mindnlp.transformers.models.roberta.configuration_roberta import RobertaConfig
from mindnlp.utils.testing_utils import DUMMY_UNKNOWN_IDENTIFIER, get_tests_dir


sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))

from test_module.custom_configuration import CustomConfig  # noqa E402


SAMPLE_ROBERTA_CONFIG = get_tests_dir("fixtures/dummy-config.json")


class AutoConfigTest(unittest.TestCase):
    def test_module_spec(self):
        self.assertIsNotNone(mindnlp.transformers.models.auto.__spec__)
        self.assertIsNotNone(importlib.util.find_spec("mindnlp.transformers.models.auto"))

    def test_config_from_model_shortcut(self):
        config = AutoConfig.from_pretrained("bert-base-uncased")
        self.assertIsInstance(config, BertConfig)

    def test_config_model_type_from_local_file(self):
        config = AutoConfig.from_pretrained(SAMPLE_ROBERTA_CONFIG)
        self.assertIsInstance(config, RobertaConfig)

    def test_config_model_type_from_model_identifier(self):
        config = AutoConfig.from_pretrained(DUMMY_UNKNOWN_IDENTIFIER, from_pt=True)
        self.assertIsInstance(config, RobertaConfig)

    def test_config_for_model_str(self):
        config = AutoConfig.for_model("roberta")
        self.assertIsInstance(config, RobertaConfig)

    def test_pattern_matching_fallback(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            # This model name contains bert and roberta, but roberta ends up being picked.
            folder = os.path.join(tmp_dir, "fake-roberta")
            os.makedirs(folder, exist_ok=True)
            with open(os.path.join(folder, "config.json"), "w") as f:
                f.write(json.dumps({}))
            config = AutoConfig.from_pretrained(folder)
            self.assertEqual(type(config), RobertaConfig)

    def test_new_config_registration(self):
        try:
            AutoConfig.register("custom", CustomConfig)
            # Wrong model type will raise an error
            with self.assertRaises(ValueError):
                AutoConfig.register("model", CustomConfig)
            # Trying to register something existing in the Transformers library will raise an error
            with self.assertRaises(ValueError):
                AutoConfig.register("bert", BertConfig)

            # Now that the config is registered, it can be used as any other config with the auto-API
            config = CustomConfig()
            with tempfile.TemporaryDirectory() as tmp_dir:
                config.save_pretrained(tmp_dir)
                new_config = AutoConfig.from_pretrained(tmp_dir)
                self.assertIsInstance(new_config, CustomConfig)

        finally:
            if "custom" in CONFIG_MAPPING._extra_content:
                del CONFIG_MAPPING._extra_content["custom"]
