import { Component, OnInit } from '@angular/core';
import { ProductService } from '../../services/product.service';

@Component({
  selector: 'app-product-list',
  templateUrl: './product-list.component.html',
  styleUrls: ['./product-list.component.css']
})
export class ProductListComponent implements OnInit {
  products: any[] = [];
  categories: any = {};
  sources: any = {};
  
  currentPage = 1;
  pageSize = 20;
  totalProducts = 0;
  
  selectedCategory: string = '';
  selectedSource: string = '';
  isLoading = false;

  constructor(private productService: ProductService) { }

  ngOnInit(): void {
    this.loadCategories();
    this.loadSources();
    this.loadProducts();
  }

  onImageError(event: Event): void {
    const img = event.target as HTMLImageElement;
    img.src = 'https://via.placeholder.com/200';
  }

  loadCategories(): void {
    this.productService.getCategories().subscribe(
      (data) => {
        this.categories = data;
      },
      (error) => console.error('Error loading categories:', error)
    );
  }

  loadSources(): void {
    this.productService.getSources().subscribe(
      (data) => {
        this.sources = data;
      },
      (error) => console.error('Error loading sources:', error)
    );
  }

  loadProducts(): void {
    this.isLoading = true;
    this.productService.getProducts(
      this.currentPage,
      this.pageSize,
      this.selectedCategory || undefined,
      this.selectedSource || undefined
    ).subscribe(
      (data) => {
        this.products = data.products;
        this.totalProducts = data.total;
        this.isLoading = false;
      },
      (error) => {
        console.error('Error loading products:', error);
        this.isLoading = false;
      }
    );
  }

  onCategoryChange(): void {
    this.currentPage = 1;
    this.loadProducts();
  }

  onSourceChange(): void {
    this.currentPage = 1;
    this.loadProducts();
  }

  nextPage(): void {
    if (this.currentPage * this.pageSize < this.totalProducts) {
      this.currentPage++;
      this.loadProducts();
    }
  }

  previousPage(): void {
    if (this.currentPage > 1) {
      this.currentPage--;
      this.loadProducts();
    }
  }

  get totalPages(): number {
    return Math.ceil(this.totalProducts / this.pageSize);
  }

  get categoryKeys(): string[] {
    return Object.keys(this.categories);
  }

  get sourceKeys(): string[] {
    return Object.keys(this.sources);
  }
}
