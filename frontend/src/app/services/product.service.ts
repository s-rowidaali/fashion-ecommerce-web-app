import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Product {
  id?: number;
  Name: string;
  Price: number;
  Link: string;
  Image: string;
  Category: string;
  Source: string;
}

export interface ProductResponse {
  total: number;
  page: number;
  limit: number;
  products: Product[];
}

export interface PriceStats {
  mean: number;
  median: number;
  min: number;
  max: number;
  std: number;
  count: number;
}

export interface SummaryStats {
  total_products: number;
  total_categories: number;
  total_sources: number;
  most_common_category: string;
  most_used_source: string;
  avg_price: number;
  highest_price: number;
  lowest_price: number;
}

export interface Distribution {
  labels: string[];
  values: number[];
}

export interface Histogram {
  labels: string[];
  frequencies: number[];
  bin_edges: number[];
}

export interface Heatmap {
  rows: string[];
  columns: string[];
  values: number[][];
  data: any;
}

export interface NetworkNode {
  id: string;
  type: 'Product' | 'Category' | 'Source';
  size: number;
  color: string;
  x: number;
  y: number;
  degree: number;
}

export interface NetworkEdge {
  source: string;
  target: string;
}

export interface NetworkGraph {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
  stats: {
    node_count: number;
    edge_count: number;
  };
}

export interface CentralityMetrics {
  top_by_degree: { node: string; value: number }[];
  top_by_betweenness: { node: string; value: number }[];
  all_degrees: { [key: string]: number };
  all_betweenness: { [key: string]: number };
}

export interface CategoryStats {
  [key: string]: {
    count: number;
    avg_price: number;
    min_price: number;
    max_price: number;
    median_price: number;
    std_price: number;
  };
}

export interface SourceStats {
  [key: string]: {
    count: number;
    avg_price: number;
    min_price: number;
    max_price: number;
    median_price: number;
    std_price: number;
  };
}

@Injectable({
  providedIn: 'root'
})
export class ProductService {
  private apiUrl = 'http://localhost:5000/api';

  constructor(private http: HttpClient) { }

  // ===== BASIC PRODUCT ENDPOINTS =====

  getProducts(page: number = 1, limit: number = 20, category?: string, source?: string): Observable<ProductResponse> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('limit', limit.toString());
    
    if (category) {
      params = params.set('category', category);
    }
    if (source) {
      params = params.set('source', source);
    }
    
    return this.http.get<ProductResponse>(`${this.apiUrl}/products`, { params });
  }

  getProduct(id: number): Observable<Product> {
    return this.http.get<Product>(`${this.apiUrl}/products/${id}`);
  }

  getCategories(): Observable<any> {
    return this.http.get(`${this.apiUrl}/categories`);
  }

  getSources(): Observable<any> {
    return this.http.get(`${this.apiUrl}/sources`);
  }

  searchProducts(query: string): Observable<any> {
    let params = new HttpParams().set('q', query);
    return this.http.get(`${this.apiUrl}/search`, { params });
  }

  getHealth(): Observable<any> {
    return this.http.get(`${this.apiUrl}/health`);
  }

  // ===== LEGACY ANALYTICS ENDPOINTS =====

  getPriceDistribution(): Observable<PriceStats> {
    return this.http.get<PriceStats>(`${this.apiUrl}/analytics/price-distribution`);
  }

  getAnalyticsByCategory(): Observable<any> {
    return this.http.get(`${this.apiUrl}/analytics/by-category`);
  }

  getAnalyticsBySource(): Observable<any> {
    return this.http.get(`${this.apiUrl}/analytics/by-source`);
  }

  // ===== NEW ANALYTICS ENDPOINTS =====

  getSummaryStats(): Observable<SummaryStats> {
    return this.http.get<SummaryStats>(`${this.apiUrl}/analytics/summary`);
  }

  getPriceHeatmap(): Observable<Heatmap> {
    return this.http.get<Heatmap>(`${this.apiUrl}/analytics/price-heatmap`);
  }

  getCategoryDistribution(): Observable<Distribution> {
    return this.http.get<Distribution>(`${this.apiUrl}/analytics/category-distribution`);
  }

  getSourceDistribution(): Observable<Distribution> {
    return this.http.get<Distribution>(`${this.apiUrl}/analytics/source-distribution`);
  }

  getPriceHistogram(): Observable<Histogram> {
    return this.http.get<Histogram>(`${this.apiUrl}/analytics/price-histogram`);
  }

  getNetworkGraph(): Observable<NetworkGraph> {
    return this.http.get<NetworkGraph>(`${this.apiUrl}/analytics/network-graph`);
  }

  getNetworkCentrality(): Observable<CentralityMetrics> {
    return this.http.get<CentralityMetrics>(`${this.apiUrl}/analytics/network-centrality`);
  }

  getCategoryStats(): Observable<CategoryStats> {
    return this.http.get<CategoryStats>(`${this.apiUrl}/analytics/category-stats`);
  }

  getSourceStats(): Observable<SourceStats> {
    return this.http.get<SourceStats>(`${this.apiUrl}/analytics/source-stats`);
  }
}
