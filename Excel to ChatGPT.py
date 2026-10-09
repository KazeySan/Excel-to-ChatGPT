
# Part 1: Uploading Excel file and selecting sheet

import streamlit as st
import pandas as pd
import requests
from pathlib import Path
import base64 

# Find folder
BASE_DIR = Path(__file__).resolve().parent

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


st.title("Send your Excel file to ChatGPT 5.6-sol")

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

def make_basic_call(prompt_text, api_key, base_url):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Title": "LLM Response",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-5.6-sol",
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
            timeout=180
        )

        # Debugging information
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
        excel_file = pd.ExcelFile(upload_file)
        sheet_names = excel_file.sheet_names

        sheet = st.selectbox(
            "Please select the sheet",
            sheet_names
        )

        df = pd.read_excel(upload_file, sheet_name=sheet)

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

                with st.spinner("Sending data to the LLM..."):
                    llm_response = make_basic_call(
                        prompt,
                        api_key,
                        base_url
                    )

                if llm_response is not None:
                    st.subheader("LLM Response")
                    st.markdown(llm_response)

    except Exception as error:
        st.error(f"Could not read the Excel file: {error}")

else:
    st.info("Please upload an Excel file to begin.")
