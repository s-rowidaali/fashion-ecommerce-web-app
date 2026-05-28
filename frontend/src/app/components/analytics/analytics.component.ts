import { Component, OnInit } from '@angular/core';
import { ProductService } from '../../services/product.service';
import { ChartConfiguration } from 'chart.js';

@Component({
  selector: 'app-analytics',
  templateUrl: './analytics.component.html',
  styleUrls: ['./analytics.component.css']
})
export class AnalyticsComponent implements OnInit {
  isLoading = true;
  
  // Summary stats
  summaryStats: any = {};
  
  // Distributions
  categoryDistribution: any = {};
  sourceDistribution: any = {};
  
  // Charts
  categoryChartData: any;
  sourceChartData: any;
  priceChartData: any;
  categoryPieData: any;
  sourcePieData: any;
  
  // Heatmap
  heatmapData: any = null;
  heatmapDisplay: any = [];
  
  // Network
  networkData: any = null;
  centralityData: any = null;
  topNodesByDegree: any[] = [];
  topNodesByBetweenness: any[] = [];
  
  // Detailed stats
  categoryStats: any = {};
  sourceStats: any = {};
  
  // Chart options
  chartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { 
        display: false 
      }
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { color: '#94a3b8', font: { size: 10 } }
      },
      y: {
        grid: { color: 'rgba(255, 255, 255, 0.05)' },
        ticks: { color: '#94a3b8', font: { size: 10 } }
      }
    }
  };

  pieChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { 
        position: 'bottom',
        labels: {
          color: '#94a3b8',
          font: { size: 9 },
          padding: 5,
          usePointStyle: true,
          boxWidth: 8
        }
      }
    }
  };

  constructor(private productService: ProductService) { }

  ngOnInit(): void {
    this.loadAllAnalytics();
  }

  loadAllAnalytics(): void {
    this.isLoading = true;

    // Load summary stats
    this.productService.getSummaryStats().subscribe(
      (data) => {
        this.summaryStats = data;
      },
      (error) => console.error('Error loading summary stats:', error)
    );

    // Load distributions for pie charts
    this.productService.getCategoryDistribution().subscribe(
      (data) => {
        this.categoryDistribution = data;
        this.prepareCategoryPieChart();
      },
      (error) => console.error('Error loading category distribution:', error)
    );

    this.productService.getSourceDistribution().subscribe(
      (data) => {
        this.sourceDistribution = data;
        this.prepareSourcePieChart();
      },
      (error) => console.error('Error loading source distribution:', error)
    );

    // Load price histogram
    this.productService.getPriceHistogram().subscribe(
      (data) => {
        this.preparePriceHistogram(data);
      },
      (error) => console.error('Error loading price histogram:', error)
    );

    // Load heatmap
    this.productService.getPriceHeatmap().subscribe(
      (data) => {
        this.heatmapData = data;
        this.prepareHeatmapDisplay();
      },
      (error) => console.error('Error loading heatmap:', error)
    );

    // Load network data
    this.productService.getNetworkGraph().subscribe(
      (data) => {
        this.networkData = data;
      },
      (error) => console.error('Error loading network graph:', error)
    );

    // Load network centrality
    this.productService.getNetworkCentrality().subscribe(
      (data) => {
        this.centralityData = data;
        this.topNodesByDegree = data.top_by_degree || [];
        this.topNodesByBetweenness = data.top_by_betweenness || [];
      },
      (error) => console.error('Error loading network centrality:', error)
    );

    // Load category stats
    this.productService.getCategoryStats().subscribe(
      (data) => {
        this.categoryStats = data;
      },
      (error) => console.error('Error loading category stats:', error)
    );

    // Load source stats
    this.productService.getSourceStats().subscribe(
      (data) => {
        this.sourceStats = data;
        this.isLoading = false;
      },
      (error) => {
        console.error('Error loading source stats:', error);
        this.isLoading = false;
      }
    );
  }

  prepareCategoryPieChart(): void {
    const colors = ['#f472b6', '#38bdf8', '#818cf8', '#c084fc', '#fb7185', '#2dd4bf', '#fbbf24', '#a8a29e'];
    
    this.categoryPieData = {
      labels: this.categoryDistribution.labels || [],
      datasets: [
        {
          data: this.categoryDistribution.values || [],
          backgroundColor: colors.slice(0, this.categoryDistribution.labels?.length || 0),
          borderColor: 'rgba(255, 255, 255, 0.1)',
          borderWidth: 1
        }
      ]
    };
  }

  prepareSourcePieChart(): void {
    const colors = ['#38bdf8', '#f472b6', '#818cf8'];
    
    this.sourcePieData = {
      labels: this.sourceDistribution.labels || [],
      datasets: [
        {
          data: this.sourceDistribution.values || [],
          backgroundColor: colors.slice(0, this.sourceDistribution.labels?.length || 0),
          borderColor: 'rgba(255, 255, 255, 0.1)',
          borderWidth: 1
        }
      ]
    };
  }

  preparePriceHistogram(data: any): void {
    this.priceChartData = {
      labels: data.labels || [],
      datasets: [
        {
          label: 'Frequency',
          data: data.frequencies || [],
          backgroundColor: 'rgba(244, 114, 182, 0.6)',
          borderColor: '#f472b6',
          borderWidth: 1
        }
      ]
    };
  }

  prepareHeatmapDisplay(): void {
    if (!this.heatmapData || !this.heatmapData.values) {
      return;
    }

    // Create a formatted display for the heatmap
    this.heatmapDisplay = this.heatmapData.rows.map((row: string, rowIndex: number) => ({
      category: row,
      values: this.heatmapData.values[rowIndex].map((val: number, colIndex: number) => ({
        source: this.heatmapData.columns[colIndex],
        price: val ? val.toFixed(0) : 'N/A'
      }))
    }));
  }

  get categoryKeys(): string[] {
    return Object.keys(this.categoryStats).sort();
  }

  get sourceKeys(): string[] {
    return Object.keys(this.sourceStats).sort();
  }

  // Helper method to get heatmap cell background color
  getHeatmapCellColor(price: string): string {
    if (price === 'N/A') return 'rgba(255, 255, 255, 0.05)';
    const numPrice = parseFloat(price);
    if (numPrice < 50) return 'rgba(56, 189, 248, 0.4)';
    if (numPrice < 100) return 'rgba(129, 140, 248, 0.4)';
    if (numPrice < 200) return 'rgba(192, 132, 252, 0.4)';
    return 'rgba(244, 114, 182, 0.6)';
  }
}
