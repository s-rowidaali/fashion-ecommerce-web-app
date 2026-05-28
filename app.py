from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import os
import json
from datetime import datetime
import numpy as np
import networkx as nx

app = Flask(__name__)
CORS(app)

# Path to data file
DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'women_fashion_clean_data.csv')

# Helper function to convert NaN to None for JSON serialization
def clean_nan(obj):
    """Replace NaN and infinite values with None for JSON serialization"""
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan(item) for item in obj]
    elif isinstance(obj, float):
        if pd.isna(obj) or np.isinf(obj):
            return None
        return obj
    return obj

# Load data function
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame()

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all products with optional filtering"""
    df = load_data()
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    # Filtering
    category = request.args.get('category', None)
    source = request.args.get('source', None)
    
    if category:
        df = df[df['Category'] == category]
    if source:
        df = df[df['Source'] == source]
    
    # Pagination
    start = (page - 1) * limit
    end = start + limit
    
    products_data = df.iloc[start:end].to_dict('records')
    
    return jsonify({
        'total': len(df),
        'page': page,
        'limit': limit,
        'products': clean_nan(products_data)
    })

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a single product by ID"""
    df = load_data()
    if product_id < len(df):
        return jsonify(df.iloc[product_id].to_dict())
    return jsonify({'error': 'Product not found'}), 404

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all categories with count"""
    df = load_data()
    categories = df['Category'].value_counts().to_dict()
    return jsonify(categories)

@app.route('/api/sources', methods=['GET'])
def get_sources():
    """Get all data sources with count"""
    df = load_data()
    sources = df['Source'].value_counts().to_dict()
    return jsonify(sources)

@app.route('/api/analytics/price-distribution', methods=['GET'])
def price_distribution():
    """Get price distribution stats"""
    df = load_data()
    df_price = df.dropna(subset=['Price'])
    
    stats = {
        'mean': float(df_price['Price'].mean()),
        'median': float(df_price['Price'].median()),
        'min': float(df_price['Price'].min()),
        'max': float(df_price['Price'].max()),
        'std': float(df_price['Price'].std()),
        'count': len(df_price)
    }
    return jsonify(stats)

@app.route('/api/analytics/by-category', methods=['GET'])
def analytics_by_category():
    """Get analytics grouped by category"""
    df = load_data()
    df_price = df.dropna(subset=['Price'])
    
    result = {}
    for category in df['Category'].unique():
        cat_data = df_price[df_price['Category'] == category]['Price']
        result[category] = {
            'count': len(cat_data),
            'avg_price': float(cat_data.mean()),
            'min_price': float(cat_data.min()),
            'max_price': float(cat_data.max())
        }
    
    return jsonify(result)

@app.route('/api/analytics/by-source', methods=['GET'])
def analytics_by_source():
    """Get analytics grouped by source"""
    df = load_data()
    df_price = df.dropna(subset=['Price'])
    
    result = {}
    for source in df['Source'].unique():
        src_data = df_price[df_price['Source'] == source]['Price']
        result[source] = {
            'count': len(src_data),
            'avg_price': float(src_data.mean()),
            'min_price': float(src_data.min()),
            'max_price': float(src_data.max())
        }
    
    return jsonify(result)

@app.route('/api/search', methods=['GET'])
def search():
    """Search products by name"""
    df = load_data()
    query = request.args.get('q', '', type=str).lower()
    
    if not query:
        return jsonify({'products': []})
    
    mask = df['Name'].str.lower().str.contains(query, na=False)
    results = df[mask].head(20).to_dict('records')
    
    return jsonify({'products': clean_nan(results)})

@app.route('/api/analytics/summary', methods=['GET'])
def get_summary_stats():
    """Get summary statistics about the dataset"""
    df = load_data()
    df_price = df.dropna(subset=['Price'])
    
    stats = {
        'total_products': len(df),
        'total_categories': int(df['Category'].nunique()),
        'total_sources': int(df['Source'].nunique()),
        'most_common_category': str(df['Category'].value_counts().idxmax()) if len(df) > 0 else 'N/A',
        'most_used_source': str(df['Source'].value_counts().idxmax()) if len(df) > 0 else 'N/A',
        'avg_price': float(df_price['Price'].mean()) if len(df_price) > 0 else 0,
        'highest_price': float(df_price['Price'].max()) if len(df_price) > 0 else 0,
        'lowest_price': float(df_price['Price'].min()) if len(df_price) > 0 else 0,
    }
    
    return jsonify(stats)

@app.route('/api/analytics/price-heatmap', methods=['GET'])
def get_price_heatmap():
    """Get average price heatmap data by category and source"""
    df = load_data()
    df_price = df.dropna(subset=['Price'])
    
    # Create pivot table
    pivot_data = df_price.pivot_table(
        values='Price',
        index='Category',
        columns='Source',
        aggfunc='mean'
    )
    
    # Convert to JSON-serializable format
    heatmap_data = {
        'rows': pivot_data.index.tolist(),
        'columns': pivot_data.columns.tolist(),
        'values': clean_nan(pivot_data.fillna(0).values.tolist()),
        'data': clean_nan(pivot_data.fillna(0).to_dict('split'))
    }
    
    return jsonify(heatmap_data)

@app.route('/api/analytics/category-distribution', methods=['GET'])
def get_category_distribution():
    """Get category distribution for pie chart"""
    df = load_data()
    
    category_counts = df['Category'].value_counts()
    
    distribution = {
        'labels': category_counts.index.tolist(),
        'values': category_counts.values.tolist()
    }
    
    return jsonify(distribution)

@app.route('/api/analytics/source-distribution', methods=['GET'])
def get_source_distribution():
    """Get source distribution for pie chart"""
    df = load_data()
    
    source_counts = df['Source'].value_counts()
    
    distribution = {
        'labels': source_counts.index.tolist(),
        'values': source_counts.values.tolist()
    }
    
    return jsonify(distribution)

@app.route('/api/analytics/price-histogram', methods=['GET'])
def get_price_histogram():
    """Get price distribution histogram data"""
    df = load_data()
    df_price = df.dropna(subset=['Price'])
    
    if len(df_price) == 0:
        return jsonify({'bins': [], 'frequencies': []})
    
    # Create histogram
    frequencies, bin_edges = np.histogram(df_price['Price'], bins=10)
    
    # Format bin labels
    bin_labels = [f"${bin_edges[i]:.2f}-${bin_edges[i+1]:.2f}" for i in range(len(bin_edges)-1)]
    
    histogram_data = {
        'labels': bin_labels,
        'frequencies': frequencies.tolist(),
        'bin_edges': bin_edges.tolist()
    }
    
    return jsonify(histogram_data)

@app.route('/api/analytics/network-graph', methods=['GET'])
def get_network_graph():
    """Get network graph data for visualization (products, categories, sources)"""
    df = load_data()
    
    # Limit data for performance
    sample_size = min(100, len(df))
    sample_df = df.sample(n=sample_size, random_state=42)
    
    # Build network
    G = nx.Graph()
    
    for idx, row in sample_df.iterrows():
        product_name = str(row['Name'])[:30]  # Truncate long names
        category = str(row['Category'])
        source = str(row['Source'])
        
        # Add nodes with type attributes
        G.add_node(product_name, node_type='Product')
        G.add_node(category, node_type='Category')
        G.add_node(source, node_type='Source')
        
        # Add edges
        G.add_edge(product_name, category)
        G.add_edge(product_name, source)
    
    # Calculate node positions using spring layout
    pos = nx.spring_layout(G, k=0.8, iterations=50, seed=42)
    
    # Calculate node degrees
    degrees = dict(G.degree())
    
    # Build node list for D3/visualization
    nodes = []
    for node in G.nodes():
        node_type = G.nodes[node].get('node_type', 'Product')
        node_size = {'Category': 20, 'Source': 15, 'Product': 5}.get(node_type, 5)
        node_color = {'Category': '#f7a8b8', 'Source': '#b8e0d2', 'Product': '#a7c7e7'}.get(node_type, '#a7c7e7')
        
        nodes.append({
            'id': node,
            'type': node_type,
            'size': node_size,
            'color': node_color,
            'x': float(pos[node][0]) * 100,
            'y': float(pos[node][1]) * 100,
            'degree': degrees.get(node, 0)
        })
    
    # Build edge list
    edges = []
    for source, target in G.edges():
        edges.append({
            'source': source,
            'target': target
        })
    
    network_data = {
        'nodes': nodes,
        'edges': edges,
        'stats': {
            'node_count': G.number_of_nodes(),
            'edge_count': G.number_of_edges()
        }
    }
    
    return jsonify(clean_nan(network_data))

@app.route('/api/analytics/network-centrality', methods=['GET'])
def get_network_centrality():
    """Get network centrality metrics (degree, betweenness)"""
    df = load_data()
    
    # Limit data for performance
    sample_size = min(100, len(df))
    sample_df = df.sample(n=sample_size, random_state=42)
    
    # Build network
    G = nx.Graph()
    
    for idx, row in sample_df.iterrows():
        product_name = str(row['Name'])[:30]
        category = str(row['Category'])
        source = str(row['Source'])
        
        G.add_node(product_name, node_type='Product')
        G.add_node(category, node_type='Category')
        G.add_node(source, node_type='Source')
        
        G.add_edge(product_name, category)
        G.add_edge(product_name, source)
    
    # Calculate metrics
    degree = dict(G.degree())
    betweenness = nx.betweenness_centrality(G)
    
    # Get top nodes by degree
    top_degree = sorted(degree.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Get top nodes by betweenness
    top_betweenness = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:10]
    
    centrality_data = {
        'top_by_degree': [{'node': node, 'value': value} for node, value in top_degree],
        'top_by_betweenness': [{'node': node, 'value': float(value)} for node, value in top_betweenness],
        'all_degrees': {node: value for node, value in degree.items()},
        'all_betweenness': {node: float(value) for node, value in betweenness.items()}
    }
    
    return jsonify(clean_nan(centrality_data))

@app.route('/api/analytics/category-stats', methods=['GET'])
def get_category_stats():
    """Get detailed statistics for each category"""
    df = load_data()
    df_price = df.dropna(subset=['Price'])
    
    stats = {}
    
    for category in df['Category'].unique():
        cat_data = df_price[df_price['Category'] == category]['Price']
        cat_count = len(df[df['Category'] == category])
        
        stats[str(category)] = {
            'count': cat_count,
            'avg_price': float(cat_data.mean()) if len(cat_data) > 0 else 0,
            'min_price': float(cat_data.min()) if len(cat_data) > 0 else 0,
            'max_price': float(cat_data.max()) if len(cat_data) > 0 else 0,
            'median_price': float(cat_data.median()) if len(cat_data) > 0 else 0,
            'std_price': float(cat_data.std()) if len(cat_data) > 0 else 0
        }
    
    return jsonify(stats)

@app.route('/api/analytics/source-stats', methods=['GET'])
def get_source_stats():
    """Get detailed statistics for each source"""
    df = load_data()
    df_price = df.dropna(subset=['Price'])
    
    stats = {}
    
    for source in df['Source'].unique():
        src_data = df_price[df_price['Source'] == source]['Price']
        src_count = len(df[df['Source'] == source])
        
        stats[str(source)] = {
            'count': src_count,
            'avg_price': float(src_data.mean()) if len(src_data) > 0 else 0,
            'min_price': float(src_data.min()) if len(src_data) > 0 else 0,
            'max_price': float(src_data.max()) if len(src_data) > 0 else 0,
            'median_price': float(src_data.median()) if len(src_data) > 0 else 0,
            'std_price': float(src_data.std()) if len(src_data) > 0 else 0
        }
    
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
