import os
import requests
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from ghost_ai_compiler.util import chat, dict_to_yaml, extract_python_code, extract_yaml, load_prompt, parse_yaml
import markdownify

def generate_specification(instruction: str):
    """
    指示文から仕様書を生成する関数。

    Args:
        instruction (str): 生成する仕様書の指示文。
    """
    if "http" in instruction:
        url_start = instruction.find("http")
        url_end = instruction.find(" ", url_start)
        if url_end == -1:
            url_end = len(instruction)
        url = instruction[url_start:url_end].strip()
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            response_text = response.text
            markdown = markdownify.markdownify(response_text, heading_style="ATX")
            instruction += f"\n\nURLの内容: {markdown}"
        except requests.RequestException as e:
            print(f"URLからデータを取得できませんでした: {e}")
            raise e

    generate_specification_prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(
            load_prompt("generate_specification_system")
        ),
        HumanMessagePromptTemplate.from_template(
            load_prompt("generate_specification_human")
        )
    ])

    generate_specification = (
        RunnablePassthrough() |
        generate_specification_prompt |
        chat |
        StrOutputParser()
    )
    result = generate_specification.invoke({
        "input": instruction
    })

    specification_result = result

    # プロジェクト名を取得
    specification = parse_yaml(specification_result)
    project_name = specification["project_name"]

    # プロジェクトのドキュメントディレクトリを作成
    project_docs_dir = f"workdir/{project_name}/docs"
    os.makedirs(project_docs_dir, exist_ok=True)

    # 仕様をYAMLファイルとして保存
    spec_file_path = f"{project_docs_dir}/modules.yaml"
    with open(spec_file_path, "w") as f:
        f.write(extract_yaml(specification_result))

    return specification

def generate_module_spec(project_name: str, module_input: str): 
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(load_prompt("generate_module_spec_system")),
        HumanMessagePromptTemplate.from_template(load_prompt("generate_module_spec_human")) 
    ])

    main = (
        RunnablePassthrough() |
        prompt |
        chat |
        StrOutputParser()
    )
    result = main.invoke({
        "input": module_input
    })
    print(f"モジュール仕様書: {result}")
    parsed_result = parse_yaml(result)

    with open(f"workdir/{project_name}/docs/{parsed_result['module_spec']['name']}.yaml", "w") as f:
        f.write(extract_yaml(result))

    return parsed_result

def impl_module_spec(project_name: str, module_name: str, module_spec: dict):
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(load_prompt("impl_module_spec_system")),
        HumanMessagePromptTemplate.from_template(load_prompt("impl_module_spec_human"))
    ])
    main = (
        RunnablePassthrough() |
        prompt |
        chat |
        StrOutputParser()
    )

    result = extract_python_code(main.invoke({
        "input": dict_to_yaml(module_spec)
    }))

    # ディレクトリを作成
    os.makedirs(f"workdir/{project_name}/src", exist_ok=True)
    with open(f"workdir/{project_name}/src/{module_name}.py", "w") as f:
        f.write(result)
        
    return result

if __name__ == "__main__":
    instructions = [
        """Hackers NewsのAPIを使用して、Hacker Newsのトップストーリーを取得するアプリ
APIの仕様は以下を確認してください。
https://github.com/HackerNews/API
        """,
        # "ToDo リストアプリ: タスクの追加、編集、削除、期限や優先度の設定ができるアプリ",
        # "計算機アプリ: 四則演算、平方根、括弧を使った計算と計算履歴の表示ができるアプリ。",
        # "タイマー・ストップウォッチアプリ: カウントダウンタイマーとストップウォッチ機能を持ち、複数のタイマーを同時に設定できるアプリ",
        # "簡単な描画アプリ: キャンバス上で線や図形を描画し、色や線の太さを変更できるアプリ",
        # "ルーレット・ランダムチョイスアプリ: 選択肢を入力し、ランダムに1つを選び、重みづけもできるアプリ",
        # "テキストエディタアプリ: シンプルなテキストの入力、編集、保存、読み込みができるアプリ",
        # "家計簿アプリ: 収入と支出を記録し、カテゴリ別に分類して集計できるアプリ",
        #  "カレンダーアプリ: 予定の追加、編集、削除ができ、日・週・月表示を切り替えられるアプリ",
        # "タッチタイピングアプリ: キーボードのキー入力練習ができ、速度と正確性を測定できるアプリ",
        # "ポモドーロタイマーアプリ: 作業と休憩時間を交互に設定し、集中力を維持するためのアプリ",
        # "シンプルな画像編集アプリ: 明るさ、コントラスト、彩度の調整や、画像の回転、トリミングができるアプリ",
        # "食事記録アプリ: 食事内容を記録し、カロリーや栄養素を計算できるアプリ",
        # "フラッシュカードアプリ: 問題と答えのカードを作成し、暗記学習ができるアプリ",
        # "シンプルな音声録音アプリ: 音声の録音、再生、保存ができるアプリ",
        # "パスワード生成アプリ: 指定した条件に基づいて、安全なパスワードを生成できるアプリ",
        # "単位変換アプリ: 長さ、重さ、温度など様々な単位を変換できるアプリ",
        # "マインドマップアプリ: アイデアを整理し、視覚的に表現できるアプリ",
        # "シンプルな家族向けチャットアプリ: テキストメッセージの送受信ができる家族向けのアプリ",
        # "瞑想アプリ: 瞑想のガイドや、リラックスできる音楽を提供するアプリ"
    ]

    for instruction in instructions:
        os.makedirs("workdir", exist_ok=True)
        try:
            print(f"指示文: {instruction}")
            specification = generate_specification(instruction)
            print(f"仕様作成完了 {specification['project_name']}")
            for module in specification["modules"]:
                module_result = generate_module_spec(specification["project_name"], dict_to_yaml(module))
                print(f"{module_result['module_spec']['name']}の仕様書作成完了")
                impl_module_spec(specification["project_name"], module["name"], module_result)
                print(f"{module_result['module_spec']['name']}の実装完了")
            print(f"poetry run streamlit run workdir/{specification['project_name']}/src/ui.py")
        except Exception as e:
            raise e
