# Import python packages
import streamlit as st
import streamlit as st
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import snowflake.connector

# 1. Fetch the robust Base64 string from secrets
b64_key_string = st.secrets["connections"]["snowflake"]["private_key"]

# 2. Decode the Base64 string back into original PEM bytes
raw_pem_bytes = base64.b64decode(b64_key_string)

# 3. Deserialize safely using cryptography
p_key = serialization.load_pem_private_key(
    raw_pem_bytes,
    password=None,
    backend=default_backend()
)

pkb = p_key.private_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

# 4. Connect to Snowflake cleanly
conn = snowflake.connector.connect(
    account=st.secrets["connections"]["snowflake"]["account"],
    user=st.secrets["connections"]["snowflake"]["user"],
    role=st.secrets["connections"]["snowflake"]["role"],
    warehouse=st.secrets["connections"]["snowflake"]["warehouse"],
    database=st.secrets["connections"]["snowflake"]["database"],
    schema=st.secrets["connections"]["snowflake"]["schema"],
    private_key=pkb
)

# Test and confirm success
cursor = conn.cursor()
cursor.execute("SELECT CURRENT_VERSION();")
st.success(f"🎉 Connected successfully! Snowflake Version: {cursor.fetchone()[0]}")


from snowflake.snowpark.functions import col

# Write directly to the app
st.title(f"Customise Your Smoothie! :cup_with_straw:")
st.write(
  """Choose the fruits you want in your Smoothie!
  """
)

name_on_order = st.text_input('Name on Smoothie:')
st.write(
  'The name on your Smoothie will be: ', name_on_order
)

cnx = st.connection("snowflake")
session = cnx.session()
                    
my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'))
#st.dataframe(data=my_dataframe, use_container_width=True)

ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:"
    , my_dataframe
    , max_selections=5
)

if ingredients_list:
    
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen +' '

    #st.write(ingredients_string)

    my_insert_stmt = """ insert into smoothies.public.orders(ingredients, name_on_order)
                    values ('""" + ingredients_string + """', '"""+ name_on_order+"""')"""

    #st.write(my_insert_stmt)
    #st.stop
    time_to_insert = st.button('Submit Order')

    if time_to_insert:
        session.sql(my_insert_stmt).collect()

        st.success('Your Smoothie is ordered, '+name_on_order+'!', icon="✅")
