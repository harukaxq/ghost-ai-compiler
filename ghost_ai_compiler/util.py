import os
import re
import yaml
from langchain.cache import SQLiteCache
from langchain_openai import ChatOpenAI
from langchain.globals import set_llm_cache

chat = ChatOpenAI(
    model="gpt-4o",
    temperature=0.0,
)

set_llm_cache(
    SQLiteCache(".cache.sqlite")
)

def extract_python_code(text: str) -> str:
    """
    stringから```python ```で囲まれた部分のみを取り出す関数。

    Args:
        text (str): Pythonコードを含む文字列。

    Returns:
        str: 抽出されたPythonコードの文字列。Pythonコードが見つからない場合は空文字列を返す。
    """
    pattern = r"```python(.*?)```"
    match = re.search(pattern, text, re.DOTALL)

    if match:
        return match.group(1).strip()
    else:
        return ""

def extract_yaml(text: str) -> str:
    """
    stringから```yaml ```で囲まれた部分のみを取り出す関数。

    Args:
        text (str): YAMLを含む文字列。

    Returns:
        str: 抽出されたYAMLの文字列。YAMLが見つからない場合は空文字列を返す。
    """
    pattern = r"```yaml(.*?)```"
    match = re.search(pattern, text, re.DOTALL)

    if match:
        return match.group(1).strip()
    else:
        return ""

def parse_yaml(yaml_str: str) -> dict:
    """
    YAMLの文字列をパースしてdictに変換する関数。

    Args:
        yaml_str (str): パースするYAMLの文字列。

    Returns:
        dict: パース結果のdict。

    Raises:
        yaml.YAMLError: YAMLのパース中にエラーが発生した場合。
    """
    try:
        return yaml.safe_load(yaml_str)
    except yaml.YAMLError:
        return yaml.safe_load(extract_yaml(yaml_str))

def dict_to_yaml(data: dict) -> str:
    """
    dictをYAMLの文字列に変換する関数。

    Args:
        data (dict): 変換するdict。

    Returns:
        str: 変換されたYAMLの文字列。
    """
    return yaml.safe_dump(data, default_flow_style=False, allow_unicode=True)

def to_dict(obj):
    """
    オブジェクトを再帰的にdictに変換する関数。

    Args:
        obj: 変換対象のオブジェクト。dictの場合はそのまま返す。

    Returns:
        dict: 変換されたdict。
    """
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    elif hasattr(obj, "__dict__"):
        return to_dict(obj.__dict__)
    elif isinstance(obj, (list, tuple)):
        return [to_dict(v) for v in obj] 
    else:
        return obj

def load_prompt(key: str) -> str:
    """
    プロンプトをロードする関数。

    Args:
        key (str): ロードするプロンプトのキー。ファイル名として使用される。
        translate (bool, optional): 英語に翻訳するかどうか。デフォルトはFalse。

    Returns:
        str: ロードされたプロンプトの内容。
    """
    prompt_dir = "ghost_ai_compiler/prompt"
    file_path = os.path.join(prompt_dir, f"{key}.txt")

    with open(file_path, "r") as f:
        prompt = f.read()

    return prompt
