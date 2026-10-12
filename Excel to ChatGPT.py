
# Part 1: Uploading Excel file and selecting sheet

import streamlit as st
import pandas as pd
import requests
from pathlib import Path
import base64 

# Find folder
BASE_DIR = Path(__file__).resolve().parent

MODEL_MAPPING = {
    "ChatGPT 5.6 Sol": "gpt-5.6-sol",
    "Claude Fable 5": "claude-fable-5",
    "Gemini 3.8 Flash": "gemini-3.8-flash",
    "DeepSeek V4.1 Flash": "deepseek-flash"
}

with open(BASE_DIR / "style.css", "r", encoding="utf-8") as file:
    css = file.read()

with open(BASE_DIR / "background.jpg", "rb") as file:
    encoded_image = base64.b64encode(file.read()).decode()

css = css.replace(
    'url("background.jpg")',
    f'url("data:image/jpeg;base64,{encoded_image}")'
)

# Apply CSS
st.markdown(
    f"<style>{css}</style>",
    unsafe_allow_html=True
)


st.title("Send your Excel file to LLMs")

with st.sidebar:
    st.header("API")
    api_key = st.text_input("Enter your API key", type="password")
    base_url = st.text_input("Enter your base URL")
    st.caption(
    "Free API keys and base URLs can be found at "
    "[api-route.com](https://api-route.com)."
    )


upload_file = st.file_uploader(
    "Upload your Excel file",
    type=["xlsx"]
)


# Part 2: The LLM Pipeline

def make_basic_call(prompt_text, api_key, base_url, model_id):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Title": "LLM Response",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model_id, 
        "messages": [
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.7,
        "max_tokens": 20000
    }

    try:
        response = requests.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
            timeout=300
        )

        st.write("HTTP status:", response.status_code)
        st.write(
            "Content type:",
            response.headers.get("Content-Type")
        )
        st.code(repr(response.text[:1000]))

        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]

        else:
            st.error(
                f"Server error {response.status_code}: "
                f"{response.text[:1000]}"
            )
            return None

    except requests.RequestException as error:
        st.error(f"Request failed: {error}")
        return None

    except (KeyError, IndexError, ValueError):
        st.error("Unexpected response format from the API.")
        return None


# Part 3: Excel selection and user prompt

if upload_file is not None:
    try:
        #Choosing the LLM Model
        LLM_SELECT= st.multiselect(
            "Select the LLM(s) you want to send the data to",
            options=list(MODEL_MAPPING.keys())
        )
        chosen_model_id = [
            MODEL_MAPPING[name]
            for name in LLM_SELECT
        ] 
        if not LLM_SELECT:
            st.warning("Please select at least one LLM")
            st.stop()

        #Uploading a file
        excel_file = pd.ExcelFile(upload_file)
        sheet_names = excel_file.sheet_names
        
        #Choosing the sheet(s)
        sheet = st.selectbox(
            "Please select the sheet",
            sheet_names
        )

        df = pd.read_excel(upload_file, sheet_name=sheet)

        #Selecting columns to send to LLM
        selected_columns = st.multiselect(
            "Select the columns you want to send to the LLM",
            options=df.columns.tolist(),
            default=df.columns.tolist()
        )

        if len(df) > 0:
            rows_columns = st.number_input(
                "Number of rows you want to send to the LLM",
                min_value=1,
                max_value=len(df),
                value=1,
                step=1
            )

            sample = df.head(int(rows_columns))[selected_columns]

            st.write("Data selected")
            st.dataframe(sample)

        else:
            st.warning("The selected sheet has no data rows.")
            sample = pd.DataFrame()

        user_prompt = st.text_area("Please enter the prompt")

        # Button to run the pipeline
        if st.button("Send to LLM"):

            if not api_key.strip():
                st.warning("Please enter your API key.")

            elif not base_url.strip():
                st.warning("Please enter your base URL.")

            elif not user_prompt.strip():
                st.warning("Please enter your prompt.")

            elif not selected_columns:
                st.warning("Please select at least one column.")

            elif sample.empty:
                st.warning("There is no data to send.")

            else:
                prompt = (
                    user_prompt
                    + "\n\nHere is the data from the Excel file:\n"
                    + sample.to_csv(index=False)
                )

                #Sending to the separate LLMs
                for model_name, model_id in zip(
                        LLM_SELECT,
                        chosen_model_id
                    ):
                        st.subheader(model_name)

                        with st.spinner(
                            f"Sending data to {model_name}..."
                        ):
                            llm_response = make_basic_call(
                                prompt,
                                api_key,
                                base_url,
                                model_id
                            )

                        if llm_response is not None:
                            st.markdown(llm_response)
                        else:
                            st.error(
                                f"{model_name} failed to respond."
                            )

    except Exception as error:
        st.error(
            f"Could not read the Excel file: {error}"
        )

else:
    st.info("Please upload an Excel file to begin.")
