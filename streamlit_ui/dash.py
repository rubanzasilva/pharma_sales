import streamlit as st
import pandas as pd
import requests
import plotly.express as px

def load_and_predict_data(csv_path):
    """
    Sends the test CSV to the BentoML API endpoint and gets predictions
    """
    files = {'csv': open(csv_path, 'rb')}
    response = requests.post(
        "http://localhost:3000/predict_csv",
        files=files
    )
    predictions = response.json()
    
    # Load the original test data
    test_df = pd.read_csv(csv_path)
    
    # Add predictions to the dataframe
    test_df['predicted_sales'] = predictions
    
    # Combine Month and Year into a single column
    test_df['month_year'] = test_df['Month'] + ' ' + test_df['Year'].astype(str)
    
    return test_df

def create_dashboard():
    """
    Creates the Streamlit dashboard with filters, KPI cards, and visualizations
    """
    st.title("Pharmaceutical Sales Prediction Dashboard")
    
    # Add custom CSS for dark theme cards
    st.markdown("""
        <style>
        .metric-card {
            background-color: #2C3333;
            padding: 20px;
            border-radius: 10px;
            margin: 10px 0;
        }
        .metric-label {
            color: #718096;
            font-size: 0.875rem;
        }
        .metric-value {
            color: white;
            font-size: 1.5rem;
            font-weight: bold;
        }
        .trend-positive {
            color: #48BB78;
        }
        .trend-negative {
            color: #F56565;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # File uploader for the test CSV
    uploaded_file = st.file_uploader("Upload test CSV file", type=['csv'])
    
    if uploaded_file is not None:
        # Save the uploaded file temporarily
        with open('temp_test.csv', 'wb') as f:
            f.write(uploaded_file.getvalue())
        
        # Load data and get predictions
        df = load_and_predict_data('temp_test.csv')
        
        # Creating filters in a sidebar
        st.sidebar.header("Filters")
        
        # Country filter
        countries = ['All'] + sorted(df['Country'].unique().tolist())
        selected_country = st.sidebar.selectbox('Select Country', countries)
        
        # Channel filter
        channels = ['All'] + sorted(df['Channel'].unique().tolist())
        selected_channel = st.sidebar.selectbox('Select Channel', channels)
        
        # Product Class filter
        product_classes = ['All'] + sorted(df['Product Class'].unique().tolist())
        selected_product_class = st.sidebar.selectbox('Select Product Class', product_classes)
        
        # Sales Team filter
        sales_teams = ['All'] + sorted(df['Sales Team'].unique().tolist())
        selected_sales_team = st.sidebar.selectbox('Select Sales Team', sales_teams)
        
        # Apply filters
        filtered_df = df.copy()
        
        if selected_country != 'All':
            filtered_df = filtered_df[filtered_df['Country'] == selected_country]
        if selected_channel != 'All':
            filtered_df = filtered_df[filtered_df['Channel'] == selected_channel]
        if selected_product_class != 'All':
            filtered_df = filtered_df[filtered_df['Product Class'] == selected_product_class]
        if selected_sales_team != 'All':
            filtered_df = filtered_df[filtered_df['Sales Team'] == selected_sales_team]
        
        # Calculate metrics for KPI cards
        total_sales = filtered_df['predicted_sales'].sum()
        avg_monthly_sales = filtered_df.groupby('month_year')['predicted_sales'].sum().mean()
        
        # Create KPI cards using columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Total Predicted Sales</div>
                    <div class="metric-value">${total_sales:,.0f}</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Average Monthly Sales</div>
                    <div class="metric-value">${avg_monthly_sales:,.0f}</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            top_distributor = (filtered_df.groupby('Distributor')['predicted_sales']
                             .sum().sort_values(ascending=False).index[0])
            distributor_sales = (filtered_df.groupby('Distributor')['predicted_sales']
                               .sum().sort_values(ascending=False).iloc[0])
            
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Top Distributor</div>
                    <div class="metric-value">{top_distributor}</div>
                    <div class="metric-label">${distributor_sales:,.0f} in sales</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col4:
            top_product = (filtered_df.groupby('Product Name')['predicted_sales']
                          .sum().sort_values(ascending=False).index[0])
            product_sales = (filtered_df.groupby('Product Name')['predicted_sales']
                           .sum().sort_values(ascending=False).iloc[0])
            
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Best Selling Product</div>
                    <div class="metric-value">{top_product}</div>
                    <div class="metric-label">${product_sales:,.0f} in sales</div>
                </div>
            """, unsafe_allow_html=True)
        
        # Group by month_year and calculate monthly total predicted sales
        monthly_sales = (filtered_df.groupby('month_year')['predicted_sales']
                        .sum()
                        .reset_index())
        
        # Sort the monthly sales by year and month
        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                      'July', 'August', 'September', 'October', 'November', 'December']
        
        # Create a sorting key
        monthly_sales['sort_key'] = monthly_sales['month_year'].apply(
            lambda x: pd.to_datetime(x, format='%B %Y')
        )
        monthly_sales = monthly_sales.sort_values('sort_key')
        
        # Create the line chart using Plotly with dark theme
        fig = px.line(
            monthly_sales,
            x='month_year',
            y='predicted_sales',
            title='Predicted Monthly Sales'
        )
        
        # Update layout for dark theme
        fig.update_layout(
            template="plotly_dark",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_title="Month-Year",
            yaxis_title="Predicted Sales",
            hovermode='x unified'
        )
        
        # Display the plot
        st.plotly_chart(fig, use_container_width=True)
        
        # Display detailed data view
        st.subheader("Detailed Data View")
        display_columns = ['month_year', 'Distributor', 'Customer Name', 'Country', 
                         'Channel', 'Product Name', 'Product Class', 
                         'Quantity', 'Price', 'predicted_sales']
        
        # Create a copy of the filtered dataframe with only the display columns
        display_df = filtered_df[display_columns].copy()
        
        # Add sort_key to display_df
        display_df['sort_key'] = pd.to_datetime(display_df['month_year'], format='%B %Y')
        
        # Sort by sort_key and drop it before display
        display_df = display_df.sort_values('sort_key').drop('sort_key', axis=1)
        
        st.dataframe(display_df, hide_index=True)

if __name__ == "__main__":
    # Set page configuration
    st.set_page_config(
        page_title="Pharmaceutical Sales Prediction Dashboard",
        page_icon="💊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    create_dashboard()