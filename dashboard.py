#import library yang dibutuhkan 
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Brazilian E-Commerce Dashboard ",
    page_icon="🛍️",
    layout="wide"
)

#css file
with open('style.css')as f:
 st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html = True)

#load data
@st.cache_data()
def load_data(url):
    #df = pd.read_excel(url)
    df = pd.read_csv(url)
    return df

# df = load_data('df_final.xlsx')
df = load_data('df_final.csv')

#convert to datetime format 
df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
df['order_approved_at'] = pd.to_datetime(df['order_approved_at'])
df['order_delivered_carrier_date'] = pd.to_datetime(df['order_delivered_carrier_date'])
df['order_delivered_customer_date'] = pd.to_datetime(df['order_delivered_customer_date']) 
df['order_estimated_delivery_date'] = pd.to_datetime(df['order_estimated_delivery_date']) 

#create dashboard title
st.header('Brazilian E-Commerce Dashboard :shopping_bags:')

#calculate order year (filtering)
df['order_year'] = df['order_purchase_timestamp'].dt.year

#preparing for metrics
m1,m2,m3,m4,m5,m6,m7,m8 = st.columns([2,2,2,2,2,2,1,4])

#5. Year Filter
with m8:
    year_opt =  st.multiselect("Order Year Options:",[2016,2017,2018], default=[2016,2017,2018])

df = df[df['order_year'].isin(year_opt)]

#1. Number of Customers
with m1:
    cust_num = df['customer_id'].nunique()
    st.metric(label="Customers", value=cust_num)

#2. Number of Sellers
with m2:
    sell_num = df['seller_id'].nunique()
    st.metric(label="Sellers", value=sell_num)

#3. Order count
with m3:
    order_cnt = df['order_id'].nunique()
    st.metric(label="Orders", value=order_cnt)

#4. Sum Sales
with m4:
    sum_sales = df[~df['order_status'].isin(['canceled','unavailable'])]['price'].sum()/1000000
    st.metric(label="Total Sales (R$)", value="{:.2f}M".format(sum_sales))

#5. Avg Freight Cost
with m5:
    freight = df[~df['order_status'].isin(['canceled','unavailable'])]['freight_value'].mean()
    st.metric(label="Avg Freight Cost (R$)", value="{:.2f}".format(freight))

#6. Avg Shipping Time
with m6:
    shipping_time = df[df['order_status'].isin(['delivered'])].dropna(subset=['order_delivered_carrier_date','order_delivered_customer_date'], axis=0)
    shipping_time['shipping_time'] = abs(shipping_time['order_delivered_customer_date']-shipping_time['order_delivered_carrier_date']).dt.total_seconds()/3600
    st.metric(label="Avg Shipping Time (h)", value=round(shipping_time['shipping_time'].mean(),2))

st.markdown('\n')
st.markdown('\n')
#preparing for visualization
#1st container (order trend, delivery performance)

viz1_cont = st.container()
with viz1_cont:
    v1,g1,v2 = st.columns([12,1,6])

    #v1 order trend
    with v1:
        st.markdown("##### Monthly Order Trend")
        viz1 = df[~df['order_status'].isin(['canceled','unavailable'])]
        viz1['year_month'] = viz1['order_purchase_timestamp'].dt.strftime('%Y-%m')
        viz1 = viz1[['year_month','order_id']].groupby('year_month').agg({'order_id':pd.Series.nunique}).reset_index().rename(columns={'year_month':'Date','order_id':'Count'})
        
        fig1 = px.line(viz1, x="Date",y="Count", markers=True, color_discrete_sequence=['#0d5c63'])
        fig1.update_layout(plot_bgcolor='#ffffff',margin=dict(l=0,r=0,b=0,t=10), height=300)
        fig1.layout.xaxis.fixedrange = True
        fig1.layout.yaxis.fixedrange = True
        fig1.update_xaxes(title='Date')
        fig1.update_yaxes(title='Count')
        st.plotly_chart(fig1, use_container_width=True)

    #v2 delivery performance
    with v2:
        st.markdown("##### Delivery Performance")
        viz2 = df[df['order_status']=='delivered']
        #calculate diff between expected - reality ship time 
        viz2 = viz2.dropna(subset='order_delivered_customer_date', axis=0)
        viz2['diff'] = (viz2['order_estimated_delivery_date']-viz2['order_delivered_customer_date']).dt.total_seconds()/3600
        #check if delivery status is late or not
        viz2['delivery_status'] = viz2['diff'].map(lambda x: 'on time' if x>0 else 'late')

        proportion = viz2[['delivery_status','order_id']].groupby('delivery_status').agg({'order_id':pd.Series.nunique})
        proportion = proportion.reset_index().rename(columns={'delivery_status':'Delivery Status', 'order_id':'Count'})
        fig2 = px.pie(proportion, values='Count', names='Delivery Status', color='Delivery Status',
                        color_discrete_map={'on time':'#44B4C1','late':'#0d5c63'}, hole=0.5)
        fig2.update_layout(plot_bgcolor='#ffffff',margin=dict(l=0,r=0,b=0,t=10), height=250)
        st.plotly_chart(fig2, use_container_width=True)

st.markdown('\n')
st.markdown('\n')
#2nd container (top products, geomap)
viz2_cont = st.container()
with viz2_cont:

    v3,g2,v4 = st.columns([8,1,11])
    #v3 top product categories
    with v3:
        st.markdown("##### Top Product Categories")
        viz3 = df[~df['order_status'].isin(['canceled','unavailable'])]
        viz3 = viz3[['product_category_name_english','product_id']].groupby(['product_category_name_english']).count().sort_values('product_id',ascending=False).head(10)
        viz3 = viz3.reset_index().rename(columns={'product_category_name_english':'Product Category','product_id':'Count'})
        viz3 = viz3.sort_values('Count',ascending=True)
        fig3 = go.Figure(go.Bar(
                        y=viz3['Product Category'],
                        x=viz3['Count'],
                        orientation='h',
                        marker_color="#0d5c63"))
        fig3.update_layout(plot_bgcolor='#ffffff',margin=dict(l=0,r=0,b=0,t=10), height=450)
        fig3.update_yaxes(title='Product Category',ticksuffix = "  ")
        fig3.update_xaxes(title='Count')
        fig3.layout.xaxis.fixedrange = True
        fig3.layout.yaxis.fixedrange = True
        st.plotly_chart(fig3, use_container_width=True)
    
    #v4 geomap
    def plot_map(df,lat,lon,txt,indicator, discrete, cat_color=None):
        if discrete == False:
            fig = px.scatter_mapbox(df, lat=lat, lon=lon, text=txt, color=indicator,size=indicator,opacity=0.8,
                  color_continuous_scale=['#ffffff','#004D54'], zoom=3,mapbox_style="carto-positron",center={'lat':-13.446,'lon':-54.396})
            fig.update_layout(margin=dict(l=0,r=0,b=0,t=0), height=400)
            return fig
        else:
            fig = px.scatter_mapbox(df, lat=lat, lon=lon, text=txt, color=cat_color, size=indicator,opacity=0.8,
                  color_discrete_sequence=['#004D54', '#fddd5c'], zoom=3,mapbox_style="carto-positron",center={'lat':-13.446,'lon':-54.396})
            fig.update_layout(margin=dict(l=0,r=0,b=0,t=0), height=400)
            return fig
    
    selected_order = df[~df['order_status'].isin(['canceled','unavailable'])]
    customer_coord = selected_order[['customer_zip_code_prefix','customer_lat','customer_lng','customer_city']].drop_duplicates()
    seller_coord = selected_order[['seller_zip_code_prefix','seller_lat','seller_lng','seller_city']].drop_duplicates()
    
    with v4:
        t4, f4 = st.columns([8,3])
        with f4:
            geo_opt = st.selectbox("Indicatior Options:",['Customers vs Sellers','Total Orders','Total Sales','Avg Freight Cost','Avg Shipping Time'], label_visibility='collapsed')
        with t4:
            (f"##### Geographic Visualization of {geo_opt}")
        if geo_opt=="Total Orders":
            viz = selected_order[['order_id','customer_zip_code_prefix']].groupby('customer_zip_code_prefix').agg({'order_id':pd.Series.nunique}).reset_index().rename(columns={'order_id':'Number of Orders'})
            viz = viz.merge(customer_coord, on='customer_zip_code_prefix', how='inner')
            fig = plot_map(df=viz, lat="customer_lat", lon="customer_lng", txt='customer_city', indicator="Number of Orders", discrete=False)
            st.plotly_chart(fig, use_container_width=True)
        
        elif geo_opt=="Total Sales":
            viz = selected_order[['price','customer_zip_code_prefix']].groupby('customer_zip_code_prefix').sum().round(2).reset_index()
            viz = viz.merge(customer_coord, on='customer_zip_code_prefix', how='inner').rename(columns={'price':'Total Sales'})
            fig = plot_map(df=viz, lat="customer_lat", lon="customer_lng", txt='customer_city', indicator="Total Sales", discrete=False)
            st.plotly_chart(fig, use_container_width=True)

        elif geo_opt=="Avg Freight Cost":
            viz = selected_order[['freight_value','customer_zip_code_prefix']].groupby('customer_zip_code_prefix').mean().round(2).reset_index()
            viz = viz.merge(customer_coord, on='customer_zip_code_prefix', how='inner').rename(columns={'freight_value':'Avg Freight Cost'})
            fig = plot_map(df=viz, lat="customer_lat", lon="customer_lng", txt='customer_city', indicator="Avg Freight Cost", discrete=False)
            st.plotly_chart(fig, use_container_width=True)

        elif geo_opt=="Avg Shipping Time":
            viz = selected_order.dropna(subset=['order_delivered_carrier_date','order_delivered_customer_date'], axis=0)
            viz['shipping_time'] = (viz['order_delivered_customer_date']-viz['order_delivered_carrier_date']).dt.total_seconds()/3600
            viz['shipping_time'] = abs(viz['shipping_time'])
            viz = viz[['shipping_time','customer_zip_code_prefix']].groupby('customer_zip_code_prefix').mean().round(2).reset_index()
            viz = viz.merge(customer_coord, on='customer_zip_code_prefix', how='inner').rename(columns={'shipping_time':'Avg Shipping Time (h)'})
            fig = plot_map(df=viz, lat="customer_lat", lon="customer_lng", txt='customer_city', indicator="Avg Shipping Time (h)", discrete=False)
            st.plotly_chart(fig, use_container_width=True)

        else:
            #customer
            cust_df = selected_order[['customer_id','customer_zip_code_prefix']].groupby('customer_zip_code_prefix').agg({'customer_id':pd.Series.nunique}).reset_index()
            cust_df = cust_df.merge(customer_coord, on='customer_zip_code_prefix', how='inner')
            cust_df = cust_df.rename(columns={'customer_zip_code_prefix':'zip_code', 'customer_id':'count', 'customer_lat':'lat',
                'customer_lng':'lng', 'customer_city':'city'})
            cust_df['Category'] = 'customer'

            #seller
            seller_df = selected_order[['seller_id','seller_zip_code_prefix']].groupby('seller_zip_code_prefix').agg({'seller_id':pd.Series.nunique}).reset_index()
            seller_df = seller_df.merge(seller_coord, on='seller_zip_code_prefix', how='inner')
            seller_df = seller_df.rename(columns={'seller_zip_code_prefix':'zip_code', 'seller_id':'count', 'seller_lat':'lat',
                'seller_lng':'lng', 'seller_city':'city'})
            seller_df['Category'] = 'seller'

            #concat two dataframes
            viz = pd.concat([cust_df,seller_df])
            fig = plot_map(df=viz, lat="lat", lon="lng", txt='city', indicator="count", discrete=True, cat_color="Category")
            st.plotly_chart(fig, use_container_width=True)