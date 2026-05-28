import { Component, OnInit } from '@angular/core';
import { ProductService } from '../../services/product.service';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit {
  stats = {
    totalProducts: 0,
    categories: 0,
    sources: 0,
    avgPrice: 0
  };
  
  recentProducts: any[] = [];
  categoryData: any = {};
  sourceData: any = {};
  isLoading = true;

  constructor(private productService: ProductService) { }

  ngOnInit(): void {
    this.loadDashboardData();
  }

  onImageError(event: Event): void {
    const img = event.target as HTMLImageElement;
    img.src = 'https://via.placeholder.com/300x400?text=Fashion+Item';
  }

  loadDashboardData(): void {
    this.productService.getProducts(1, 12).subscribe(
      (data) => {
        this.stats.totalProducts = data.total;
        this.recentProducts = data.products;
      },
      (error) => console.error('Error loading products:', error)
    );

    this.productService.getCategories().subscribe(
      (data) => {
        this.categoryData = data;
        this.stats.categories = Object.keys(data).length;
      },
      (error) => console.error('Error loading categories:', error)
    );

    this.productService.getSources().subscribe(
      (data) => {
        this.sourceData = data;
        this.stats.sources = Object.keys(data).length;
      },
      (error) => console.error('Error loading sources:', error)
    );

    this.productService.getPriceDistribution().subscribe(
      (data) => {
        this.stats.avgPrice = Math.round(data.mean);
        this.isLoading = false;
      },
      (error) => {
        console.error('Error loading price data:', error);
        this.isLoading = false;
      }
    );
  }
}
