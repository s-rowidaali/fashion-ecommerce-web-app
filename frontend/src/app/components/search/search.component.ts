import { Component } from '@angular/core';
import { ProductService } from '../../services/product.service';

@Component({
  selector: 'app-search',
  templateUrl: './search.component.html',
  styleUrls: ['./search.component.css']
})
export class SearchComponent {
  searchQuery = '';
  searchResults: any[] = [];
  isSearching = false;

  constructor(private productService: ProductService) { }

  search(): void {
    if (!this.searchQuery.trim()) {
      this.searchResults = [];
      return;
    }

    this.isSearching = true;
    this.productService.searchProducts(this.searchQuery).subscribe(
      (data) => {
        this.searchResults = data.products;
        this.isSearching = false;
      },
      (error) => {
        console.error('Error searching products:', error);
        this.isSearching = false;
      }
    );
  }
}
