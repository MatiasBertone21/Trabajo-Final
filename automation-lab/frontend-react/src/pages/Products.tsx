import { useState, useEffect } from 'react';
import { productService } from '../services/productService';
import { ProductCard } from '../components/product/ProductCard';
import type { Product } from '../types/product';

export const Products = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  // Filtros
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [prods, cats] = await Promise.all([
          productService.getAll(),
          productService.getCategories()
        ]);
        setProducts(prods);
        setCategories(['All', ...cats]);
      } catch {
        setError(true);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

    if (loading) return <div data-testid="loading-state">Cargando productos...</div>;
    if (error) return <div data-testid="error-state">Error al cargar el catálogo.</div>;

    const filtered = products.filter(p => 
        (selectedCategory === 'All' || p.category === selectedCategory) &&
        p.name.toLowerCase().includes(search.toLowerCase())
    );

  return (
    <div data-testid="products-page" className="page-shell">
      <div className="filters-row">
        <div className="input-group">
          <label htmlFor="search-input">Buscar</label>
          <input
            id="search-input"
            data-testid="search-input"
            placeholder="Buscar..."
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="input-group">
          <label htmlFor="category-filter">Categoría</label>
          <select
            id="category-filter"
            data-testid="category-filter"
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            {categories.map(cat => <option key={cat} value={cat}>{cat}</option>)}
          </select>
        </div>
      </div>

      {filtered.length > 0 ? (
        <div className="grid-responsive">
          {filtered.map(p => <ProductCard key={p.id} product={p} />)}
        </div>
      ) : (
        <div className="empty-state" data-testid="empty-products">No hay productos.</div>
      )}
    </div>
  );
};