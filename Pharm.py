import pandas as pd
import openai
import streamlit as st
import openpyxl

openai.api_key = "MY_API-KEY_HERE"

data = pd.read_excel('Данные.xlsx', sheet_name='data', engine='openpyxl')
data2 = pd.read_excel('Binipharm.xlsx', sheet_name='Sheet9', engine='openpyxl')

data2_cleared = data2[['id_kommunikacii', 'nazvanie_kommunikacii', 'tekst_kommunikacii', 'brand', 'target', 'sent', 'delivered', 'opened', 'clicked']]

data2_cleared = data2_cleared.drop_duplicates()

data = data.dropna(axis=0, subset = 'oblastId')

data = data.drop(columns=['istochnik', 'kanal', 'oblastId',	'oblast',	'sent',	'delivered',	'opened',	'clicked',	'unsubscribed'])

data = data.drop_duplicates()

sms = data[
    (data['channel'] == 'sms') &
    (data['tekst_kommunikacii'] != 'No Brand_Внешние смс') &
    (~data['tekst_kommunikacii'].str.contains('БФГ|Напоминание о вебинаре|смс-рассылка|СМС|Смс_Отправка|Дексонал_Отправка|БфгГ|SMS|Смс', na=False))
]

merged_data = sms.merge(data2_cleared, on=['id_kommunikacii', 'nazvanie_kommunikacii', 'tekst_kommunikacii', 'brand', 'target'], how='left')

merged_data.info()

md = merged_data.drop_duplicates()

md=md.dropna()

md['conversion'] = md['opened']/md['delivered']

# Группировка по бренду и тексту, затем сортировка внутри каждой группы по конверсии
sorted_groups = md.groupby(['brand', 'tekst_kommunikacii']).apply(lambda x: x.sort_values('conversion', ascending=False)).reset_index(drop=True)

# Оставляем только самое высокое значение конверсии для каждой группы
top_conversion_texts = sorted_groups.drop_duplicates(subset=['brand', 'tekst_kommunikacii'], keep='first')

# Сортируем результаты сначала по бренду, затем по конверсии
result = top_conversion_texts.sort_values(by=['brand', 'conversion'], ascending=[True, False])

final_result = result[result['conversion'] > 0.000001]
final_result = final_result[final_result['conversion'] < 1]

# Получаем список всех уникальных брендов
unique_brands = final_result['brand'].unique()

st.write("Приложение для настройки текста коммуникации")

# Создаем селектбокс для выбора бренда
brand_name = st.selectbox('Выберите бренд:', unique_brands)

# Фильтруем DataFrame на основе выбранного бренда
filtered_data = final_result[final_result['brand'] == brand_name]

# Выбираем нужные столбцы
small_dataset = filtered_data[['tekst_kommunikacii', 'conversion']]

# Выводим небольшой датасет
st.write(small_dataset.sort_values(by='conversion', ascending=False).reset_index(drop=True))

# Создаем второй селектбокс для выбора текста коммуникации
message = st.selectbox('Выберите текст коммуникации:', small_dataset['tekst_kommunikacii'].unique())

initial_content = f'Напиши на русском языке 4 варианта текста до 130 знаков каждый для бренда {brand_name} аналогичный {message}'
edited_content = st.text_area("Текст запроса для нейросети:", value=initial_content)

if st.button("Отправить запрос нейросети"):
    completion = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=[
        {"role": "user", "content": edited_content}])

    response_content = completion["choices"][0]["message"]["content"]
    
    st.write("Варианты SMS-сообщений")
    
    st.write(response_content)
