"""
Timeline visualization generator for legal chronologies.
Creates interactive timelines, relationship graphs, and chronological charts.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
from collections import defaultdict
import base64
import io

from .timeline_extractor import Timeline, TimelineEvent, EventType, EventCertainty
from .chronology_analyzer import ChronologyInsights, TemporalPattern
from .relationship_mapper import RelationshipNetwork, EventRelationship, RelationshipType

logger = logging.getLogger(__name__)


class VisualizationType(Enum):
    """Types of timeline visualizations."""
    LINEAR_TIMELINE = "linear_timeline"
    INTERACTIVE_TIMELINE = "interactive_timeline"
    GANTT_CHART = "gantt_chart"
    NETWORK_GRAPH = "network_graph"
    CALENDAR_VIEW = "calendar_view"
    SWIMLANE_DIAGRAM = "swimlane_diagram"
    SANKEY_DIAGRAM = "sankey_diagram"
    HEATMAP = "heatmap"
    STATISTICAL_CHARTS = "statistical_charts"


class OutputFormat(Enum):
    """Output formats for visualizations."""
    HTML = "html"
    SVG = "svg"
    PNG = "png"
    PDF = "pdf"
    JSON = "json"
    INTERACTIVE_HTML = "interactive_html"


@dataclass
class VisualizationConfig:
    """Configuration for timeline visualization."""
    visualization_type: VisualizationType
    output_format: OutputFormat
    
    # Styling options
    width: int = 1200
    height: int = 600
    color_scheme: str = "professional"  # professional, colorful, grayscale
    theme: str = "light"  # light, dark
    
    # Content options
    show_confidence: bool = True
    show_relationships: bool = True
    show_patterns: bool = True
    show_gaps: bool = True
    show_entities: bool = True
    
    # Filtering options
    event_types: List[EventType] = field(default_factory=list)
    date_range: Optional[Tuple[datetime, datetime]] = None
    min_confidence: float = 0.0
    
    # Interactive options
    enable_zoom: bool = True
    enable_pan: bool = True
    enable_hover: bool = True
    enable_click_details: bool = True
    
    # Export options
    include_legend: bool = True
    include_summary: bool = True
    title: str = "Legal Timeline"
    subtitle: str = ""


@dataclass
class VisualizationOutput:
    """Output from timeline visualization."""
    visualization_id: str
    config: VisualizationConfig
    content: str  # HTML, SVG, or other format content
    metadata: Dict[str, Any] = field(default_factory=dict)
    creation_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Additional files (for complex visualizations)
    additional_files: Dict[str, str] = field(default_factory=dict)
    
    # Statistics
    events_displayed: int = 0
    relationships_displayed: int = 0
    date_range_displayed: Optional[Tuple[datetime, datetime]] = None


class TimelineVisualizer:
    """Creates various types of timeline visualizations for legal chronologies."""
    
    def __init__(self):
        """Initialize timeline visualizer."""
        
        # Color schemes
        self.color_schemes = {
            'professional': {
                'primary': '#2C3E50',
                'secondary': '#3498DB',
                'accent': '#E74C3C',
                'success': '#27AE60',
                'warning': '#F39C12',
                'info': '#8E44AD',
                'background': '#FFFFFF',
                'text': '#2C3E50',
                'border': '#BDC3C7'
            },
            'colorful': {
                'primary': '#FF6B6B',
                'secondary': '#4ECDC4',
                'accent': '#45B7D1',
                'success': '#96CEB4',
                'warning': '#FFEAA7',
                'info': '#DDA0DD',
                'background': '#FFFFFF',
                'text': '#2D3436',
                'border': '#74B9FF'
            },
            'grayscale': {
                'primary': '#2D3436',
                'secondary': '#636E72',
                'accent': '#B2BEC3',
                'success': '#00B894',
                'warning': '#FDCB6E',
                'info': '#6C5CE7',
                'background': '#FFFFFF',
                'text': '#2D3436',
                'border': '#DDD'
            }
        }
        
        # Event type colors
        self.event_colors = {
            EventType.FILING: '#3498DB',
            EventType.HEARING: '#E74C3C',
            EventType.MOTION: '#9B59B6',
            EventType.ORDER: '#E67E22',
            EventType.DISCOVERY: '#1ABC9C',
            EventType.DEPOSITION: '#34495E',
            EventType.SETTLEMENT: '#27AE60',
            EventType.TRIAL: '#C0392B',
            EventType.CONTRACT: '#8E44AD',
            EventType.DEADLINE: '#F39C12',
            EventType.COMMUNICATION: '#16A085',
            EventType.PAYMENT: '#2ECC71',
            EventType.MEETING: '#95A5A6',
            EventType.UNKNOWN: '#BDC3C7'
        }
        
    def create_visualization(self, timeline: Timeline,
                           config: VisualizationConfig,
                           insights: ChronologyInsights = None,
                           relationships: RelationshipNetwork = None) -> VisualizationOutput:
        """Create timeline visualization based on configuration.
        
        Args:
            timeline: Timeline to visualize
            config: Visualization configuration
            insights: Optional chronology insights
            relationships: Optional relationship network
            
        Returns:
            Visualization output
        """
        logger.info(f"Creating {config.visualization_type.value} visualization")
        
        # Filter events based on configuration
        filtered_events = self._filter_events(timeline.events, config)
        
        # Generate visualization based on type
        if config.visualization_type == VisualizationType.LINEAR_TIMELINE:
            content = self._create_linear_timeline(filtered_events, config, insights)
        elif config.visualization_type == VisualizationType.INTERACTIVE_TIMELINE:
            content = self._create_interactive_timeline(filtered_events, config, insights, relationships)
        elif config.visualization_type == VisualizationType.GANTT_CHART:
            content = self._create_gantt_chart(filtered_events, config)
        elif config.visualization_type == VisualizationType.NETWORK_GRAPH:
            content = self._create_network_graph(filtered_events, config, relationships)
        elif config.visualization_type == VisualizationType.CALENDAR_VIEW:
            content = self._create_calendar_view(filtered_events, config)
        elif config.visualization_type == VisualizationType.SWIMLANE_DIAGRAM:
            content = self._create_swimlane_diagram(filtered_events, config)
        elif config.visualization_type == VisualizationType.HEATMAP:
            content = self._create_heatmap(filtered_events, config)
        elif config.visualization_type == VisualizationType.STATISTICAL_CHARTS:
            content = self._create_statistical_charts(filtered_events, config, insights)
        else:
            raise ValueError(f"Unsupported visualization type: {config.visualization_type}")
        
        # Calculate date range displayed
        dated_events = [e for e in filtered_events if e.date]
        date_range_displayed = None
        if dated_events:
            dates = [e.date for e in dated_events]
            date_range_displayed = (min(dates), max(dates))
        
        return VisualizationOutput(
            visualization_id=f"viz_{timeline.timeline_id}_{int(datetime.utcnow().timestamp())}",
            config=config,
            content=content,
            events_displayed=len(filtered_events),
            relationships_displayed=len(relationships.event_relationships) if relationships else 0,
            date_range_displayed=date_range_displayed,
            metadata={
                'timeline_id': timeline.timeline_id,
                'creation_method': config.visualization_type.value,
                'total_timeline_events': len(timeline.events)
            }
        )
    
    def _filter_events(self, events: List[TimelineEvent], config: VisualizationConfig) -> List[TimelineEvent]:
        """Filter events based on configuration criteria."""
        filtered = events
        
        # Filter by event types
        if config.event_types:
            filtered = [e for e in filtered if e.event_type in config.event_types]
        
        # Filter by confidence
        if config.min_confidence > 0:
            filtered = [e for e in filtered if e.confidence >= config.min_confidence]
        
        # Filter by date range
        if config.date_range and config.date_range[0] and config.date_range[1]:
            start_date, end_date = config.date_range
            filtered = [e for e in filtered if e.date and start_date <= e.date <= end_date]
        
        return filtered
    
    def _create_linear_timeline(self, events: List[TimelineEvent], 
                              config: VisualizationConfig,
                              insights: ChronologyInsights = None) -> str:
        """Create a linear timeline visualization."""
        
        # Sort events by date
        dated_events = [e for e in events if e.date]
        dated_events.sort(key=lambda x: x.date)
        
        colors = self.color_schemes[config.color_scheme]
        
        if config.output_format == OutputFormat.HTML:
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{config.title}</title>
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background-color: {colors['background']};
                        color: {colors['text']};
                    }}
                    .timeline-container {{
                        max-width: {config.width}px;
                        margin: 0 auto;
                    }}
                    .timeline-header {{
                        text-align: center;
                        margin-bottom: 30px;
                    }}
                    .timeline-header h1 {{
                        color: {colors['primary']};
                        margin: 0;
                        font-size: 2.5em;
                    }}
                    .timeline-header h2 {{
                        color: {colors['secondary']};
                        margin: 10px 0;
                        font-weight: normal;
                        font-size: 1.2em;
                    }}
                    .timeline {{
                        position: relative;
                        padding-left: 30px;
                    }}
                    .timeline::before {{
                        content: '';
                        position: absolute;
                        left: 15px;
                        top: 0;
                        bottom: 0;
                        width: 2px;
                        background: {colors['border']};
                    }}
                    .timeline-event {{
                        position: relative;
                        margin-bottom: 30px;
                        padding: 20px;
                        background: white;
                        border-left: 4px solid {colors['primary']};
                        border-radius: 5px;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                        margin-left: 30px;
                    }}
                    .timeline-event::before {{
                        content: '';
                        position: absolute;
                        left: -42px;
                        top: 25px;
                        width: 12px;
                        height: 12px;
                        border-radius: 50%;
                        background: {colors['primary']};
                        border: 3px solid {colors['background']};
                    }}
                    .event-date {{
                        font-weight: bold;
                        color: {colors['primary']};
                        font-size: 0.9em;
                        margin-bottom: 8px;
                    }}
                    .event-type {{
                        display: inline-block;
                        padding: 3px 8px;
                        background: {colors['secondary']};
                        color: white;
                        border-radius: 3px;
                        font-size: 0.8em;
                        font-weight: bold;
                        margin-bottom: 10px;
                    }}
                    .event-description {{
                        line-height: 1.5;
                        margin-bottom: 10px;
                    }}
                    .event-meta {{
                        font-size: 0.8em;
                        color: {colors['secondary']};
                        border-top: 1px solid {colors['border']};
                        padding-top: 10px;
                        margin-top: 10px;
                    }}
                    .confidence-bar {{
                        width: 100%;
                        height: 4px;
                        background: {colors['border']};
                        border-radius: 2px;
                        margin: 5px 0;
                        overflow: hidden;
                    }}
                    .confidence-fill {{
                        height: 100%;
                        background: {colors['success']};
                        border-radius: 2px;
                    }}
                    .participants {{
                        margin: 5px 0;
                    }}
                    .participant {{
                        display: inline-block;
                        padding: 2px 6px;
                        background: {colors['info']};
                        color: white;
                        border-radius: 10px;
                        font-size: 0.7em;
                        margin: 2px;
                    }}
                    .timeline-gaps {{
                        background: {colors['warning']};
                        border: 1px dashed {colors['accent']};
                        padding: 15px;
                        margin: 20px 30px;
                        border-radius: 5px;
                        text-align: center;
                        color: {colors['text']};
                    }}
                </style>
            </head>
            <body>
                <div class="timeline-container">
                    <div class="timeline-header">
                        <h1>{config.title}</h1>
                        {f'<h2>{config.subtitle}</h2>' if config.subtitle else ''}
                    </div>
                    <div class="timeline">
            """
            
            # Add events to timeline
            prev_date = None
            for event in dated_events:
                # Check for significant gaps
                if prev_date and config.show_gaps:
                    gap_days = (event.date - prev_date).days
                    if gap_days > 30:  # Show gaps larger than 30 days
                        html += f"""
                        <div class="timeline-gaps">
                            📅 Gap of {gap_days} days ({prev_date.strftime('%Y-%m-%d')} to {event.date.strftime('%Y-%m-%d')})
                        </div>
                        """
                
                # Event color based on type
                event_color = self.event_colors.get(event.event_type, colors['primary'])
                
                html += f"""
                <div class="timeline-event" style="border-left-color: {event_color};">
                    <div class="event-date">{event.date.strftime('%B %d, %Y')}</div>
                    <div class="event-type" style="background: {event_color};">{event.event_type.value.replace('_', ' ').title()}</div>
                    <div class="event-description">{event.description}</div>
                    <div class="event-meta">
                        <div><strong>Certainty:</strong> {event.certainty.value.title()}</div>
                """
                
                if config.show_confidence:
                    html += f"""
                        <div><strong>Confidence:</strong> {event.confidence:.2f}
                            <div class="confidence-bar">
                                <div class="confidence-fill" style="width: {event.confidence * 100}%;"></div>
                            </div>
                        </div>
                    """
                
                if config.show_entities and event.participants:
                    html += f"""
                        <div class="participants">
                            <strong>Participants:</strong>
                            {' '.join(f'<span class="participant">{p}</span>' for p in event.participants)}
                        </div>
                    """
                
                if event.amount:
                    html += f"<div><strong>Amount:</strong> {event.amount}</div>"
                
                if event.location:
                    html += f"<div><strong>Location:</strong> {event.location}</div>"
                
                html += """
                    </div>
                </div>
                """
                
                prev_date = event.date
            
            # Add undated events
            undated_events = [e for e in events if not e.date]
            if undated_events:
                html += f"""
                <div class="timeline-gaps">
                    <h3>Undated Events ({len(undated_events)} events)</h3>
                </div>
                """
                
                for event in undated_events:
                    event_color = self.event_colors.get(event.event_type, colors['primary'])
                    html += f"""
                    <div class="timeline-event" style="border-left-color: {event_color}; opacity: 0.7;">
                        <div class="event-type" style="background: {event_color};">{event.event_type.value.replace('_', ' ').title()}</div>
                        <div class="event-description">{event.description}</div>
                    </div>
                    """
            
            html += """
                    </div>
                </div>
            </body>
            </html>
            """
            
            return html
            
        elif config.output_format == OutputFormat.SVG:
            return self._create_svg_timeline(dated_events, config)
        
        else:
            raise ValueError(f"Unsupported output format for linear timeline: {config.output_format}")
    
    def _create_interactive_timeline(self, events: List[TimelineEvent],
                                   config: VisualizationConfig,
                                   insights: ChronologyInsights = None,
                                   relationships: RelationshipNetwork = None) -> str:
        """Create an interactive timeline using D3.js."""
        
        dated_events = [e for e in events if e.date]
        dated_events.sort(key=lambda x: x.date)
        
        colors = self.color_schemes[config.color_scheme]
        
        # Prepare event data for JavaScript
        events_data = []
        for event in dated_events:
            event_data = {
                'id': event.event_id,
                'date': event.date.isoformat(),
                'type': event.event_type.value,
                'description': event.description[:100] + '...' if len(event.description) > 100 else event.description,
                'full_description': event.description,
                'confidence': event.confidence,
                'certainty': event.certainty.value,
                'participants': event.participants,
                'location': event.location,
                'amount': event.amount,
                'color': self.event_colors.get(event.event_type, colors['primary'])
            }
            events_data.append(event_data)
        
        # Prepare relationship data
        relationships_data = []
        if relationships and config.show_relationships:
            for rel in relationships.event_relationships:
                # Only include relationships between events we're displaying
                source_in_events = any(e.event_id == rel.source_event_id for e in dated_events)
                target_in_events = any(e.event_id == rel.target_event_id for e in dated_events)
                
                if source_in_events and target_in_events:
                    relationships_data.append({
                        'source': rel.source_event_id,
                        'target': rel.target_event_id,
                        'type': rel.relationship_type.value,
                        'strength': rel.strength.value,
                        'confidence': rel.confidence,
                        'description': rel.description
                    })
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{config.title}</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: {colors['background']};
                    color: {colors['text']};
                }}
                .timeline-container {{
                    max-width: {config.width}px;
                    margin: 0 auto;
                }}
                .timeline-header {{
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .timeline-header h1 {{
                    color: {colors['primary']};
                    margin: 0;
                }}
                .timeline-svg {{
                    border: 1px solid {colors['border']};
                    background: white;
                    border-radius: 5px;
                }}
                .event-circle {{
                    cursor: pointer;
                    transition: all 0.3s;
                }}
                .event-circle:hover {{
                    stroke-width: 3px;
                    r: 8;
                }}
                .event-label {{
                    pointer-events: none;
                    text-anchor: middle;
                    font-size: 11px;
                    fill: {colors['text']};
                }}
                .relationship-line {{
                    stroke: {colors['secondary']};
                    stroke-opacity: 0.6;
                    stroke-width: 1.5;
                    marker-end: url(#arrowhead);
                }}
                .timeline-axis {{
                    font-size: 12px;
                }}
                .tooltip {{
                    position: absolute;
                    background: {colors['primary']};
                    color: white;
                    padding: 10px;
                    border-radius: 5px;
                    font-size: 12px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                    pointer-events: none;
                    opacity: 0;
                    transition: opacity 0.3s;
                    max-width: 300px;
                }}
                .controls {{
                    margin: 20px 0;
                    text-align: center;
                }}
                .control-button {{
                    padding: 5px 15px;
                    margin: 0 5px;
                    background: {colors['secondary']};
                    color: white;
                    border: none;
                    border-radius: 3px;
                    cursor: pointer;
                }}
                .control-button:hover {{
                    background: {colors['primary']};
                }}
                .legend {{
                    margin-top: 20px;
                    padding: 15px;
                    background: white;
                    border-radius: 5px;
                    border: 1px solid {colors['border']};
                }}
                .legend-item {{
                    display: inline-block;
                    margin: 5px 10px;
                    font-size: 12px;
                }}
                .legend-color {{
                    display: inline-block;
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    margin-right: 5px;
                    vertical-align: middle;
                }}
            </style>
        </head>
        <body>
            <div class="timeline-container">
                <div class="timeline-header">
                    <h1>{config.title}</h1>
                    {f'<p>{config.subtitle}</p>' if config.subtitle else ''}
                </div>
                
                <div class="controls">
                    <button class="control-button" onclick="zoomIn()">Zoom In</button>
                    <button class="control-button" onclick="zoomOut()">Zoom Out</button>
                    <button class="control-button" onclick="resetZoom()">Reset</button>
                    <button class="control-button" onclick="toggleRelationships()">Toggle Relationships</button>
                </div>
                
                <svg class="timeline-svg" width="{config.width}" height="{config.height}"></svg>
                
                <div class="tooltip"></div>
                
                {self._generate_legend(events, colors) if config.include_legend else ''}
            </div>
            
            <script>
                const eventsData = {json.dumps(events_data)};
                const relationshipsData = {json.dumps(relationships_data)};
                
                // D3.js timeline implementation
                {self._generate_d3_timeline_script(config)}
            </script>
        </body>
        </html>
        """
        
        return html
    
    def _create_gantt_chart(self, events: List[TimelineEvent], config: VisualizationConfig) -> str:
        """Create a Gantt chart visualization."""
        
        # Group events by participants for swim lanes
        participant_events = defaultdict(list)
        for event in events:
            if event.date:
                if event.participants:
                    for participant in event.participants:
                        participant_events[participant].append(event)
                else:
                    participant_events["Unassigned"].append(event)
        
        colors = self.color_schemes[config.color_scheme]
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{config.title}</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: {colors['background']};
                }}
                .gantt-container {{
                    max-width: {config.width}px;
                    margin: 0 auto;
                }}
                .gantt-header {{
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .gantt-chart {{
                    background: white;
                    border: 1px solid {colors['border']};
                    border-radius: 5px;
                }}
                .gantt-row {{
                    height: 40px;
                    border-bottom: 1px solid {colors['border']};
                }}
                .gantt-row:nth-child(even) {{
                    background: #f9f9f9;
                }}
                .gantt-label {{
                    font-size: 12px;
                    font-weight: bold;
                    padding: 10px;
                    width: 150px;
                    display: inline-block;
                    vertical-align: top;
                    background: {colors['primary']};
                    color: white;
                }}
                .gantt-bar {{
                    height: 20px;
                    border-radius: 3px;
                    margin: 10px 5px;
                    cursor: pointer;
                    position: relative;
                }}
                .gantt-bar-label {{
                    position: absolute;
                    left: 5px;
                    top: 3px;
                    font-size: 10px;
                    color: white;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="gantt-container">
                <div class="gantt-header">
                    <h1>{config.title}</h1>
                </div>
                <div class="gantt-chart" id="gantt-chart">
                    <!-- Gantt chart will be rendered here -->
                </div>
            </div>
            
            <script>
                // Gantt chart implementation
                const participantEvents = {json.dumps({k: [{'date': e.date.isoformat(), 'type': e.event_type.value, 'description': e.description} for e in v if e.date] for k, v in participant_events.items()})};
                
                {self._generate_gantt_script(config)}
            </script>
        </body>
        </html>
        """
        
        return html
    
    def _create_network_graph(self, events: List[TimelineEvent],
                             config: VisualizationConfig,
                             relationships: RelationshipNetwork = None) -> str:
        """Create a network graph visualization of event relationships."""
        
        if not relationships:
            return "<p>No relationship data available for network graph.</p>"
        
        colors = self.color_schemes[config.color_scheme]
        
        # Prepare nodes and links
        nodes = []
        for event in events:
            nodes.append({
                'id': event.event_id,
                'name': event.description[:50] + '...' if len(event.description) > 50 else event.description,
                'type': event.event_type.value,
                'date': event.date.isoformat() if event.date else None,
                'confidence': event.confidence,
                'color': self.event_colors.get(event.event_type, colors['primary'])
            })
        
        links = []
        event_ids = set(e.event_id for e in events)
        for rel in relationships.event_relationships:
            if rel.source_event_id in event_ids and rel.target_event_id in event_ids:
                links.append({
                    'source': rel.source_event_id,
                    'target': rel.target_event_id,
                    'type': rel.relationship_type.value,
                    'strength': rel.confidence,
                    'description': rel.description
                })
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{config.title} - Network Graph</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: {colors['background']};
                }}
                .network-container {{
                    max-width: {config.width}px;
                    margin: 0 auto;
                    text-align: center;
                }}
                .network-svg {{
                    border: 1px solid {colors['border']};
                    background: white;
                    border-radius: 5px;
                }}
                .node {{
                    cursor: pointer;
                    stroke: white;
                    stroke-width: 2px;
                }}
                .link {{
                    stroke: {colors['secondary']};
                    stroke-opacity: 0.6;
                    marker-end: url(#arrowhead);
                }}
                .node-label {{
                    pointer-events: none;
                    text-anchor: middle;
                    font-size: 10px;
                    fill: {colors['text']};
                }}
                .controls {{
                    margin: 20px 0;
                }}
                .control-button {{
                    padding: 8px 16px;
                    margin: 0 5px;
                    background: {colors['secondary']};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }}
            </style>
        </head>
        <body>
            <div class="network-container">
                <h1>{config.title} - Relationship Network</h1>
                
                <div class="controls">
                    <button class="control-button" onclick="restartSimulation()">Reset Layout</button>
                    <button class="control-button" onclick="toggleLabels()">Toggle Labels</button>
                </div>
                
                <svg class="network-svg" width="{config.width}" height="{config.height}"></svg>
            </div>
            
            <script>
                const nodes = {json.dumps(nodes)};
                const links = {json.dumps(links)};
                
                {self._generate_network_script(config)}
            </script>
        </body>
        </html>
        """
        
        return html
    
    def _create_calendar_view(self, events: List[TimelineEvent], config: VisualizationConfig) -> str:
        """Create a calendar view of events."""
        
        dated_events = [e for e in events if e.date]
        if not dated_events:
            return "<p>No dated events available for calendar view.</p>"
        
        # Group events by date
        events_by_date = defaultdict(list)
        for event in dated_events:
            date_key = event.date.strftime('%Y-%m-%d')
            events_by_date[date_key].append(event)
        
        colors = self.color_schemes[config.color_scheme]
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{config.title} - Calendar View</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: {colors['background']};
                }}
                .calendar-container {{
                    max-width: {config.width}px;
                    margin: 0 auto;
                }}
                .calendar-header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .calendar-grid {{
                    display: grid;
                    grid-template-columns: repeat(7, 1fr);
                    gap: 1px;
                    background: {colors['border']};
                    border: 1px solid {colors['border']};
                }}
                .calendar-day-header {{
                    background: {colors['primary']};
                    color: white;
                    text-align: center;
                    padding: 10px;
                    font-weight: bold;
                    font-size: 14px;
                }}
                .calendar-day {{
                    background: white;
                    min-height: 100px;
                    padding: 5px;
                    position: relative;
                }}
                .calendar-day-number {{
                    font-weight: bold;
                    margin-bottom: 5px;
                }}
                .calendar-event {{
                    background: {colors['secondary']};
                    color: white;
                    padding: 2px 4px;
                    margin: 1px 0;
                    border-radius: 2px;
                    font-size: 9px;
                    cursor: pointer;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }}
                .calendar-event:hover {{
                    background: {colors['primary']};
                }}
                .other-month {{
                    color: #ccc;
                    background: #f9f9f9;
                }}
                .event-indicator {{
                    position: absolute;
                    bottom: 3px;
                    right: 3px;
                    background: {colors['accent']};
                    color: white;
                    border-radius: 50%;
                    width: 16px;
                    height: 16px;
                    font-size: 10px;
                    text-align: center;
                    line-height: 16px;
                }}
            </style>
        </head>
        <body>
            <div class="calendar-container">
                <div class="calendar-header">
                    <h1>{config.title} - Calendar View</h1>
                </div>
                
                {self._generate_calendar_html(events_by_date, config)}
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _create_swimlane_diagram(self, events: List[TimelineEvent], config: VisualizationConfig) -> str:
        """Create a swimlane diagram grouped by participants."""
        
        # Group events by participants (swimlanes)
        swimlanes = defaultdict(list)
        for event in events:
            if event.date:
                if event.participants:
                    for participant in event.participants:
                        swimlanes[participant].append(event)
                else:
                    swimlanes["Unassigned"].append(event)
        
        # Sort events in each swimlane by date
        for participant in swimlanes:
            swimlanes[participant].sort(key=lambda x: x.date)
        
        colors = self.color_schemes[config.color_scheme]
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{config.title} - Swimlane Diagram</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: {colors['background']};
                }}
                .swimlane-container {{
                    max-width: {config.width}px;
                    margin: 0 auto;
                }}
                .swimlane-header {{
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .swimlane {{
                    border: 1px solid {colors['border']};
                    margin-bottom: 10px;
                    background: white;
                    border-radius: 5px;
                    overflow: hidden;
                }}
                .swimlane-label {{
                    background: {colors['primary']};
                    color: white;
                    padding: 10px;
                    font-weight: bold;
                    width: 150px;
                    display: inline-block;
                    vertical-align: top;
                }}
                .swimlane-content {{
                    display: inline-block;
                    width: calc(100% - 170px);
                    min-height: 60px;
                    padding: 10px;
                    position: relative;
                }}
                .swimlane-event {{
                    display: inline-block;
                    background: {colors['secondary']};
                    color: white;
                    padding: 5px 10px;
                    margin: 2px;
                    border-radius: 15px;
                    font-size: 12px;
                    cursor: pointer;
                }}
                .swimlane-event:hover {{
                    background: {colors['primary']};
                }}
            </style>
        </head>
        <body>
            <div class="swimlane-container">
                <div class="swimlane-header">
                    <h1>{config.title} - Swimlane View</h1>
                </div>
                
                {self._generate_swimlane_html(swimlanes, config)}
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _create_heatmap(self, events: List[TimelineEvent], config: VisualizationConfig) -> str:
        """Create a heatmap showing event density over time."""
        
        dated_events = [e for e in events if e.date]
        if not dated_events:
            return "<p>No dated events available for heatmap.</p>"
        
        # Create monthly activity heatmap
        monthly_activity = defaultdict(int)
        for event in dated_events:
            month_key = event.date.strftime('%Y-%m')
            monthly_activity[month_key] += 1
        
        colors = self.color_schemes[config.color_scheme]
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{config.title} - Activity Heatmap</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: {colors['background']};
                }}
                .heatmap-container {{
                    max-width: {config.width}px;
                    margin: 0 auto;
                    text-align: center;
                }}
                .heatmap-svg {{
                    background: white;
                    border: 1px solid {colors['border']};
                    border-radius: 5px;
                }}
                .heatmap-cell {{
                    stroke: white;
                    stroke-width: 1px;
                }}
                .heatmap-label {{
                    font-size: 12px;
                    fill: {colors['text']};
                    text-anchor: middle;
                }}
            </style>
        </head>
        <body>
            <div class="heatmap-container">
                <h1>{config.title} - Activity Heatmap</h1>
                <svg class="heatmap-svg" width="{config.width}" height="{config.height}"></svg>
            </div>
            
            <script>
                const monthlyData = {json.dumps(monthly_activity)};
                {self._generate_heatmap_script(config)}
            </script>
        </body>
        </html>
        """
        
        return html
    
    def _create_statistical_charts(self, events: List[TimelineEvent],
                                  config: VisualizationConfig,
                                  insights: ChronologyInsights = None) -> str:
        """Create statistical charts and visualizations."""
        
        colors = self.color_schemes[config.color_scheme]
        
        # Event type distribution
        event_type_counts = defaultdict(int)
        for event in events:
            event_type_counts[event.event_type.value] += 1
        
        # Confidence distribution
        confidence_ranges = defaultdict(int)
        for event in events:
            if event.confidence >= 0.8:
                confidence_ranges['High (0.8-1.0)'] += 1
            elif event.confidence >= 0.5:
                confidence_ranges['Medium (0.5-0.8)'] += 1
            else:
                confidence_ranges['Low (0.0-0.5)'] += 1
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{config.title} - Statistics</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: {colors['background']};
                }}
                .stats-container {{
                    max-width: {config.width}px;
                    margin: 0 auto;
                }}
                .stats-header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .chart-section {{
                    background: white;
                    margin: 20px 0;
                    padding: 20px;
                    border-radius: 8px;
                    border: 1px solid {colors['border']};
                }}
                .chart-title {{
                    color: {colors['primary']};
                    margin-bottom: 15px;
                    font-size: 1.3em;
                }}
                .stats-summary {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .stat-card {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    border: 1px solid {colors['border']};
                    text-align: center;
                }}
                .stat-number {{
                    font-size: 2em;
                    font-weight: bold;
                    color: {colors['primary']};
                }}
                .stat-label {{
                    color: {colors['secondary']};
                    font-size: 0.9em;
                    margin-top: 5px;
                }}
            </style>
        </head>
        <body>
            <div class="stats-container">
                <div class="stats-header">
                    <h1>{config.title} - Timeline Statistics</h1>
                </div>
                
                <div class="stats-summary">
                    <div class="stat-card">
                        <div class="stat-number">{len(events)}</div>
                        <div class="stat-label">Total Events</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{len([e for e in events if e.date])}</div>
                        <div class="stat-label">Dated Events</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{len(set(e.event_type for e in events))}</div>
                        <div class="stat-label">Event Types</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{sum(e.confidence for e in events) / len(events):.2f}</div>
                        <div class="stat-label">Avg Confidence</div>
                    </div>
                </div>
                
                <div class="chart-section">
                    <h3 class="chart-title">Event Type Distribution</h3>
                    <svg id="event-type-chart" width="600" height="300"></svg>
                </div>
                
                <div class="chart-section">
                    <h3 class="chart-title">Confidence Distribution</h3>
                    <svg id="confidence-chart" width="600" height="300"></svg>
                </div>
            </div>
            
            <script>
                const eventTypeData = {json.dumps(event_type_counts)};
                const confidenceData = {json.dumps(confidence_ranges)};
                
                {self._generate_statistics_script(config)}
            </script>
        </body>
        </html>
        """
        
        return html
    
    # Helper methods for generating JavaScript and HTML components
    
    def _generate_legend(self, events: List[TimelineEvent], colors: Dict[str, str]) -> str:
        """Generate legend HTML for event types."""
        event_types = set(e.event_type for e in events)
        
        legend_html = f"""
        <div class="legend">
            <h4>Event Types</h4>
        """
        
        for event_type in sorted(event_types, key=lambda x: x.value):
            color = self.event_colors.get(event_type, colors['primary'])
            legend_html += f"""
            <div class="legend-item">
                <span class="legend-color" style="background-color: {color};"></span>
                {event_type.value.replace('_', ' ').title()}
            </div>
            """
        
        legend_html += "</div>"
        return legend_html
    
    def _generate_d3_timeline_script(self, config: VisualizationConfig) -> str:
        """Generate D3.js script for interactive timeline."""
        return f"""
        const svg = d3.select('.timeline-svg');
        const width = {config.width};
        const height = {config.height};
        const margin = {{top: 50, right: 50, bottom: 50, left: 50}};
        
        let showRelationships = {str(config.show_relationships).lower()};
        
        // Parse dates
        eventsData.forEach(d => d.date = new Date(d.date));
        
        // Create scales
        const xScale = d3.scaleTime()
            .domain(d3.extent(eventsData, d => d.date))
            .range([margin.left, width - margin.right]);
        
        const yScale = d3.scaleBand()
            .domain(eventsData.map(d => d.type))
            .range([margin.top, height - margin.bottom])
            .padding(0.1);
        
        // Create axes
        svg.append('g')
            .attr('transform', `translate(0,${{height - margin.bottom}})`)
            .call(d3.axisBottom(xScale));
        
        svg.append('g')
            .attr('transform', `translate(${{margin.left}},0)`)
            .call(d3.axisLeft(yScale));
        
        // Add events
        const events = svg.selectAll('.event-circle')
            .data(eventsData)
            .enter().append('circle')
            .attr('class', 'event-circle')
            .attr('cx', d => xScale(d.date))
            .attr('cy', d => yScale(d.type) + yScale.bandwidth() / 2)
            .attr('r', d => 3 + d.confidence * 7)
            .attr('fill', d => d.color)
            .attr('stroke', '#fff')
            .attr('stroke-width', 2);
        
        // Add event labels
        svg.selectAll('.event-label')
            .data(eventsData)
            .enter().append('text')
            .attr('class', 'event-label')
            .attr('x', d => xScale(d.date))
            .attr('y', d => yScale(d.type) - 10)
            .text(d => d.description.substring(0, 20) + '...');
        
        // Add tooltip
        const tooltip = d3.select('.tooltip');
        
        events.on('mouseover', function(event, d) {{
            tooltip.style('opacity', 1)
                .style('left', (event.pageX + 10) + 'px')
                .style('top', (event.pageY - 10) + 'px')
                .html(`
                    <strong>${{d.type.replace('_', ' ').toUpperCase()}}</strong><br/>
                    Date: ${{d.date.toDateString()}}<br/>
                    Description: ${{d.full_description}}<br/>
                    Confidence: ${{d.confidence.toFixed(2)}}<br/>
                    ${{d.participants.length > 0 ? 'Participants: ' + d.participants.join(', ') : ''}}
                `);
        }})
        .on('mouseout', function() {{
            tooltip.style('opacity', 0);
        }});
        
        // Zoom functionality
        let zoom = d3.zoom()
            .scaleExtent([0.1, 10])
            .on('zoom', function(event) {{
                const transform = event.transform;
                svg.selectAll('.event-circle')
                    .attr('transform', transform);
                svg.selectAll('.event-label')
                    .attr('transform', transform);
                svg.select('g')
                    .call(d3.axisBottom(xScale.copy().range([margin.left * transform.k + transform.x, (width - margin.right) * transform.k + transform.x])));
            }});
        
        if ({str(config.enable_zoom).lower()}) {{
            svg.call(zoom);
        }}
        
        // Control functions
        function zoomIn() {{
            svg.transition().call(zoom.scaleBy, 1.5);
        }}
        
        function zoomOut() {{
            svg.transition().call(zoom.scaleBy, 0.67);
        }}
        
        function resetZoom() {{
            svg.transition().call(zoom.transform, d3.zoomIdentity);
        }}
        
        function toggleRelationships() {{
            showRelationships = !showRelationships;
            // Implementation for toggling relationships
        }}
        """
    
    def _generate_gantt_script(self, config: VisualizationConfig) -> str:
        """Generate script for Gantt chart."""
        return """
        // Simple Gantt chart implementation
        console.log('Gantt chart data:', participantEvents);
        """
    
    def _generate_network_script(self, config: VisualizationConfig) -> str:
        """Generate script for network graph."""
        return f"""
        const svg = d3.select('.network-svg');
        const width = {config.width};
        const height = {config.height};
        
        const simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(links).id(d => d.id))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2));
        
        const link = svg.append('g')
            .selectAll('line')
            .data(links)
            .enter().append('line')
            .attr('class', 'link')
            .attr('stroke-width', d => Math.sqrt(d.strength * 5));
        
        const node = svg.append('g')
            .selectAll('circle')
            .data(nodes)
            .enter().append('circle')
            .attr('class', 'node')
            .attr('r', d => 5 + d.confidence * 10)
            .attr('fill', d => d.color)
            .call(d3.drag()
                .on('start', dragstarted)
                .on('drag', dragged)
                .on('end', dragended));
        
        const label = svg.append('g')
            .selectAll('text')
            .data(nodes)
            .enter().append('text')
            .attr('class', 'node-label')
            .text(d => d.name)
            .attr('dy', 3);
        
        simulation.on('tick', () => {{
            link.attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
            
            node.attr('cx', d => d.x)
                .attr('cy', d => d.y);
            
            label.attr('x', d => d.x)
                .attr('y', d => d.y);
        }});
        
        function dragstarted(event, d) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}
        
        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}
        
        function dragended(event, d) {{
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}
        
        function restartSimulation() {{
            simulation.alpha(1).restart();
        }}
        
        function toggleLabels() {{
            label.style('opacity', label.style('opacity') == 0 ? 1 : 0);
        }}
        """
    
    def _generate_calendar_html(self, events_by_date: Dict[str, List[TimelineEvent]], 
                               config: VisualizationConfig) -> str:
        """Generate HTML for calendar view."""
        # Simplified calendar implementation
        calendar_html = """
        <div class="calendar-grid">
            <div class="calendar-day-header">Sun</div>
            <div class="calendar-day-header">Mon</div>
            <div class="calendar-day-header">Tue</div>
            <div class="calendar-day-header">Wed</div>
            <div class="calendar-day-header">Thu</div>
            <div class="calendar-day-header">Fri</div>
            <div class="calendar-day-header">Sat</div>
        """
        
        # Add calendar days with events (simplified implementation)
        for i in range(35):  # 5 weeks
            calendar_html += f"""
            <div class="calendar-day">
                <div class="calendar-day-number">{i % 31 + 1}</div>
                <!-- Events would be added here -->
            </div>
            """
        
        calendar_html += "</div>"
        return calendar_html
    
    def _generate_swimlane_html(self, swimlanes: Dict[str, List[TimelineEvent]], 
                               config: VisualizationConfig) -> str:
        """Generate HTML for swimlane diagram."""
        swimlane_html = ""
        
        for participant, events in swimlanes.items():
            swimlane_html += f"""
            <div class="swimlane">
                <div class="swimlane-label">{participant}</div>
                <div class="swimlane-content">
            """
            
            for event in events:
                swimlane_html += f"""
                <div class="swimlane-event" title="{event.description}">
                    {event.event_type.value.replace('_', ' ').title()}
                </div>
                """
            
            swimlane_html += """
                </div>
            </div>
            """
        
        return swimlane_html
    
    def _generate_heatmap_script(self, config: VisualizationConfig) -> str:
        """Generate script for heatmap visualization."""
        return """
        const svg = d3.select('.heatmap-svg');
        const data = Object.entries(monthlyData).map(([month, count]) => ({month, count}));
        
        const maxCount = d3.max(data, d => d.count);
        const colorScale = d3.scaleSequential(d3.interpolateBlues)
            .domain([0, maxCount]);
        
        const cellSize = 50;
        const cols = 12;
        
        svg.selectAll('.heatmap-cell')
            .data(data)
            .enter()
            .append('rect')
            .attr('class', 'heatmap-cell')
            .attr('x', (d, i) => (i % cols) * cellSize)
            .attr('y', (d, i) => Math.floor(i / cols) * cellSize)
            .attr('width', cellSize - 2)
            .attr('height', cellSize - 2)
            .attr('fill', d => colorScale(d.count));
        
        svg.selectAll('.heatmap-label')
            .data(data)
            .enter()
            .append('text')
            .attr('class', 'heatmap-label')
            .attr('x', (d, i) => (i % cols) * cellSize + cellSize/2)
            .attr('y', (d, i) => Math.floor(i / cols) * cellSize + cellSize/2)
            .text(d => d.count);
        """
    
    def _generate_statistics_script(self, config: VisualizationConfig) -> str:
        """Generate script for statistical charts."""
        return """
        // Event type bar chart
        const eventTypeChart = d3.select('#event-type-chart');
        const eventTypes = Object.entries(eventTypeData);
        
        const xScale = d3.scaleBand()
            .domain(eventTypes.map(d => d[0]))
            .range([50, 550])
            .padding(0.1);
        
        const yScale = d3.scaleLinear()
            .domain([0, d3.max(eventTypes, d => d[1])])
            .range([250, 50]);
        
        eventTypeChart.selectAll('.bar')
            .data(eventTypes)
            .enter()
            .append('rect')
            .attr('class', 'bar')
            .attr('x', d => xScale(d[0]))
            .attr('y', d => yScale(d[1]))
            .attr('width', xScale.bandwidth())
            .attr('height', d => 250 - yScale(d[1]))
            .attr('fill', '#3498DB');
        
        eventTypeChart.append('g')
            .attr('transform', 'translate(0,250)')
            .call(d3.axisBottom(xScale));
        
        eventTypeChart.append('g')
            .attr('transform', 'translate(50,0)')
            .call(d3.axisLeft(yScale));
        
        // Confidence pie chart
        const confidenceChart = d3.select('#confidence-chart');
        const confidenceTypes = Object.entries(confidenceData);
        const radius = 100;
        
        const pie = d3.pie().value(d => d[1]);
        const arc = d3.arc().innerRadius(0).outerRadius(radius);
        
        const g = confidenceChart.append('g')
            .attr('transform', `translate(300,150)`);
        
        g.selectAll('.arc')
            .data(pie(confidenceTypes))
            .enter()
            .append('g')
            .attr('class', 'arc')
            .append('path')
            .attr('d', arc)
            .attr('fill', (d, i) => d3.schemeCategory10[i]);
        """
    
    def _create_svg_timeline(self, events: List[TimelineEvent], config: VisualizationConfig) -> str:
        """Create SVG timeline visualization."""
        # Simplified SVG timeline implementation
        svg_content = f"""
        <svg width="{config.width}" height="{config.height}" xmlns="http://www.w3.org/2000/svg">
            <text x="50" y="30" font-family="Arial" font-size="20" fill="#2C3E50">{config.title}</text>
            <!-- Timeline events would be rendered here -->
        </svg>
        """
        return svg_content
    
    def create_multi_view_dashboard(self, timeline: Timeline,
                                   insights: ChronologyInsights = None,
                                   relationships: RelationshipNetwork = None) -> VisualizationOutput:
        """Create a comprehensive dashboard with multiple visualization views."""
        
        colors = self.color_schemes['professional']
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Legal Timeline Dashboard</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: {colors['background']};
                }}
                .dashboard-container {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    grid-template-rows: auto 1fr 1fr;
                    gap: 20px;
                    padding: 20px;
                    min-height: 100vh;
                }}
                .dashboard-header {{
                    grid-column: 1 / -1;
                    text-align: center;
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    border: 1px solid {colors['border']};
                }}
                .dashboard-panel {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    border: 1px solid {colors['border']};
                    overflow: auto;
                }}
                .panel-title {{
                    color: {colors['primary']};
                    margin-bottom: 15px;
                    font-size: 1.2em;
                    border-bottom: 2px solid {colors['border']};
                    padding-bottom: 5px;
                }}
            </style>
        </head>
        <body>
            <div class="dashboard-container">
                <div class="dashboard-header">
                    <h1>Legal Timeline Dashboard</h1>
                    <p>Comprehensive analysis of {timeline.timeline_id}</p>
                </div>
                
                <div class="dashboard-panel">
                    <h3 class="panel-title">Linear Timeline</h3>
                    <!-- Linear timeline visualization -->
                </div>
                
                <div class="dashboard-panel">
                    <h3 class="panel-title">Event Statistics</h3>
                    <!-- Statistical charts -->
                </div>
                
                <div class="dashboard-panel">
                    <h3 class="panel-title">Relationship Network</h3>
                    <!-- Network graph -->
                </div>
                
                <div class="dashboard-panel">
                    <h3 class="panel-title">Activity Heatmap</h3>
                    <!-- Heatmap visualization -->
                </div>
            </div>
        </body>
        </html>
        """
        
        config = VisualizationConfig(
            visualization_type=VisualizationType.INTERACTIVE_TIMELINE,
            output_format=OutputFormat.HTML,
            title="Legal Timeline Dashboard"
        )
        
        return VisualizationOutput(
            visualization_id=f"dashboard_{timeline.timeline_id}",
            config=config,
            content=html,
            events_displayed=len(timeline.events),
            metadata={'type': 'dashboard', 'panels': 4}
        )
    
    def export_visualization(self, output: VisualizationOutput, 
                           export_format: OutputFormat) -> str:
        """Export visualization to different formats."""
        
        if export_format == OutputFormat.HTML:
            return output.content
        elif export_format == OutputFormat.JSON:
            return json.dumps({
                'visualization_id': output.visualization_id,
                'content': output.content,
                'metadata': output.metadata,
                'creation_timestamp': output.creation_timestamp.isoformat()
            }, indent=2)
        else:
            raise ValueError(f"Export format {export_format} not yet supported")
    
    def get_visualization_statistics(self, output: VisualizationOutput) -> Dict[str, Any]:
        """Get statistics about the visualization."""
        
        return {
            'visualization_id': output.visualization_id,
            'visualization_type': output.config.visualization_type.value,
            'output_format': output.config.output_format.value,
            'events_displayed': output.events_displayed,
            'relationships_displayed': output.relationships_displayed,
            'date_range': [
                output.date_range_displayed[0].isoformat() if output.date_range_displayed else None,
                output.date_range_displayed[1].isoformat() if output.date_range_displayed else None
            ],
            'content_size_chars': len(output.content),
            'creation_timestamp': output.creation_timestamp.isoformat(),
            'config': {
                'width': output.config.width,
                'height': output.config.height,
                'color_scheme': output.config.color_scheme,
                'theme': output.config.theme,
                'interactive_features': {
                    'zoom': output.config.enable_zoom,
                    'pan': output.config.enable_pan,
                    'hover': output.config.enable_hover,
                    'click_details': output.config.enable_click_details
                }
            }
        }