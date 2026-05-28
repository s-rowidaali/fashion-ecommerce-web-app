import { Component, OnInit, ViewChild, ElementRef, Input, OnChanges, SimpleChanges, AfterViewInit, OnDestroy } from '@angular/core';
import * as d3 from 'd3';

@Component({
  selector: 'app-network-visualization',
  templateUrl: './network-visualization.component.html',
  styleUrls: ['./network-visualization.component.css']
})
export class NetworkVisualizationComponent implements OnInit, OnChanges, AfterViewInit, OnDestroy {
  @Input() networkData: any;
  @ViewChild('networkContainer') networkContainer!: ElementRef;

  private svg: any;
  private simulation: any;
  private resizeObserver: ResizeObserver | null = null;
  private isInitialized = false;

  constructor() { }

  ngOnInit(): void { }

  ngAfterViewInit(): void {
    this.isInitialized = true;
    if (this.networkData) {
      // Use a small timeout to ensure container has dimensions
      setTimeout(() => this.createNetworkVisualization(), 100);
    }

    // Handle resizing
    this.resizeObserver = new ResizeObserver(() => {
      if (this.networkData) {
        this.createNetworkVisualization();
      }
    });
    this.resizeObserver.observe(this.networkContainer.nativeElement);
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['networkData'] && this.isInitialized) {
      this.createNetworkVisualization();
    }
  }

  ngOnDestroy(): void {
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
    }
    if (this.simulation) {
      this.simulation.stop();
    }
  }

  createNetworkVisualization(): void {
    if (!this.networkContainer || !this.networkData || !this.networkData.nodes || !this.networkData.edges) {
      return;
    }

    const container = this.networkContainer.nativeElement;
    const width = container.clientWidth;
    const height = container.clientHeight;

    if (width === 0 || height === 0) return;

    // Deep copy data to prevent D3 from mutating the original input
    // This is CRITICAL because D3 replaces ID strings with object references
    const nodes = this.networkData.nodes.map((d: any) => ({ ...d }));
    const links = this.networkData.edges.map((d: any) => ({ ...d }));

    // Clear previous SVG
    d3.select(container).selectAll('svg').remove();

    // Create SVG
    this.svg = d3.select(container)
      .append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', [0, 0, width, height]);

    const g = this.svg.append('g');

    // Add zoom behavior
    const zoom = d3.zoom()
      .scaleExtent([0.1, 8])
      .on('zoom', (event: any) => {
        g.attr('transform', event.transform);
      });
    
    this.svg.call(zoom);

    // Create force simulation
    this.simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id((d: any) => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-400))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius((d: any) => d.size + 15));

    // Create links
    const link = g.selectAll('.link')
      .data(links)
      .enter()
      .append('line')
      .attr('class', 'link')
      .attr('stroke', 'rgba(255, 255, 255, 0.15)')
      .attr('stroke-width', 1.5);

    // Create node groups
    const node = g.selectAll('.node')
      .data(nodes)
      .enter()
      .append('g')
      .attr('class', 'node')
      .call(d3.drag()
        .on('start', (event: any, d: any) => {
          if (!event.active) this.simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event: any, d: any) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event: any, d: any) => {
          if (!event.active) this.simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        }));

    // Add circles to nodes
    node.append('circle')
      .attr('r', (d: any) => d.size)
      .attr('fill', (d: any) => d.color)
      .attr('stroke', 'rgba(255, 255, 255, 0.3)')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer');

    // Add labels to nodes
    node.append('text')
      .attr('dy', (d: any) => d.size + 12)
      .attr('text-anchor', 'middle')
      .attr('fill', '#94a3b8')
      .attr('font-size', '10px')
      .style('pointer-events', 'none')
      .text((d: any) => d.id.length > 12 ? d.id.substring(0, 10) + '...' : d.id);

    // Add hover effects
    node.on('mouseover', (event: any, d: any) => {
      d3.select(event.currentTarget).select('circle')
        .transition().duration(200)
        .attr('r', d.size * 1.5)
        .attr('stroke', '#fff');
      
      link.transition().duration(200)
        .attr('stroke', (l: any) => 
          (l.source.id === d.id || l.target.id === d.id) ? '#f472b6' : 'rgba(255, 255, 255, 0.05)'
        )
        .attr('stroke-width', (l: any) => 
          (l.source.id === d.id || l.target.id === d.id) ? 3 : 1
        );
    })
    .on('mouseout', (event: any, d: any) => {
      d3.select(event.currentTarget).select('circle')
        .transition().duration(200)
        .attr('r', d.size)
        .attr('stroke', 'rgba(255, 255, 255, 0.3)');
      
      link.transition().duration(200)
        .attr('stroke', 'rgba(255, 255, 255, 0.15)')
        .attr('stroke-width', 1.5);
    });

    // Update positions on tick
    this.simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });

    // Initial fit to center
    this.svg.call(zoom.transform, d3.zoomIdentity.translate(0, 0));
  }
}

