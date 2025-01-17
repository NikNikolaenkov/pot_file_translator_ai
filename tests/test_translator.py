import pytest
from unittest.mock import Mock, patch, MagicMock
from src.translator import PotTranslator
from src.config import Config
import os

class TestPotTranslator:
    @pytest.fixture
    def mock_openai(self, mocker):
        # Створюємо мок для відповіді
        mock_message = MagicMock()
        mock_message.content = "Привіт ||| Світ"
        
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        
        # Створюємо мок для chat.completions.create
        mock_create = MagicMock(return_value=mock_response)
        
        # Створюємо мок для chat.completions
        mock_completions = MagicMock()
        mock_completions.create = mock_create
        
        # Створюємо мок для chat
        mock_chat = MagicMock()
        mock_chat.completions = mock_completions
        
        # Створюємо мок для клієнта OpenAI
        mock_client = MagicMock()
        mock_client.chat = mock_chat
        
        # Патчимо конструктор OpenAI
        mocker.patch('src.translator.OpenAI', return_value=mock_client)
        
        return mock_client

    @pytest.fixture
    def translator(self, mock_openai):
        return PotTranslator(api_key="test-key")

    @pytest.fixture
    def sample_pot_file(self, tmp_path):
        content = '''msgid ""
msgstr ""
"Project-Id-Version: Test\\n"
"Content-Type: text/plain; charset=UTF-8\\n"

msgid "Hello"
msgstr ""

msgid "World"
msgstr ""
'''
        pot_file = tmp_path / "test.pot"
        pot_file.write_text(content)
        return str(pot_file)

    def test_translate_batch(self, translator, mock_openai):
        texts = ["Hello", "World"]
        result = translator.translate_batch(texts, "uk")
        
        # Перевіряємо, що create було викликано з правильними параметрами
        mock_openai.chat.completions.create.assert_called_once_with(
            model=Config.DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": "Translate to uk. Each sentence is separated by '|||'."},
                {"role": "user", "content": "Hello ||| World"}
            ]
        )
        
        assert result == ["Привіт", "Світ"]

    def test_translate_pot_file(self, translator, sample_pot_file, mock_openai, tmp_path):
        with patch('os.makedirs'):
            target_language = "uk"
            output_file = translator.translate_pot_file(sample_pot_file, target_language)
            
            # Перевіряємо, що create було викликано
            assert mock_openai.chat.completions.create.called
            
            # Перевіряємо параметри виклику
            mock_openai.chat.completions.create.assert_called_with(
                model=Config.DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": "Translate to uk. Each sentence is separated by '|||'."},
                    {"role": "user", "content": "Hello ||| World"}
                ]
            )
            
            assert output_file.endswith(f"{target_language}.po") 