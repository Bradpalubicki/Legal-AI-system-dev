import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'
import { ExportConfig, ExportFormat, ReportTemplate, DashboardWidget } from '../types/analytics'

export class ExportService {
  /**
   * Export a single chart or component to various formats
   */
  static async exportChart(element: HTMLElement, config: ExportConfig): Promise<Blob> {
    const { format, quality = 'high' } = config
    
    switch (format) {
      case ExportFormat.PNG:
        return this.exportToPNG(element, quality)
      
      case ExportFormat.JPEG:
        return this.exportToJPEG(element, quality)
      
      case ExportFormat.PDF:
        return this.exportToPDF(element, config)
      
      case ExportFormat.SVG:
        return this.exportToSVG(element)
      
      default:
        throw new Error(`Unsupported export format: ${format}`)
    }
  }

  /**
   * Export chart data to CSV or JSON
   */
  static async exportData(data: any[], config: ExportConfig): Promise<Blob> {
    const { format } = config
    
    switch (format) {
      case ExportFormat.CSV:
        return this.exportToCSV(data)
      
      case ExportFormat.JSON:
        return this.exportToJSON(data)
      
      case ExportFormat.EXCEL:
        return this.exportToExcel(data)
      
      default:
        throw new Error(`Unsupported data export format: ${format}`)
    }
  }

  /**
   * Generate a complete report from template
   */
  static async generateReport(
    template: ReportTemplate, 
    widgets: DashboardWidget[],
    widgetElements: Map<string, HTMLElement>
  ): Promise<Blob> {
    switch (template.format) {
      case ExportFormat.PDF:
        return this.generatePDFReport(template, widgets, widgetElements)
      
      case ExportFormat.EXCEL:
        return this.generateExcelReport(template, widgets)
      
      default:
        throw new Error(`Unsupported report format: ${template.format}`)
    }
  }

  // Private export methods
  private static async exportToPNG(element: HTMLElement, quality: string): Promise<Blob> {
    const scale = quality === 'high' ? 2 : quality === 'medium' ? 1.5 : 1
    
    const canvas = await html2canvas(element, {
      scale,
      useCORS: true,
      allowTaint: true,
      backgroundColor: '#ffffff'
    })
    
    return new Promise((resolve) => {
      canvas.toBlob((blob) => {
        resolve(blob!)
      }, 'image/png')
    })
  }

  private static async exportToJPEG(element: HTMLElement, quality: string): Promise<Blob> {
    const qualityValue = quality === 'high' ? 0.9 : quality === 'medium' ? 0.7 : 0.5
    const canvas = await html2canvas(element, {
      scale: 2,
      useCORS: true,
      allowTaint: true,
      backgroundColor: '#ffffff'
    })
    
    return new Promise((resolve) => {
      canvas.toBlob((blob) => {
        resolve(blob!)
      }, 'image/jpeg', qualityValue)
    })
  }

  private static async exportToPDF(element: HTMLElement, config: ExportConfig): Promise<Blob> {
    const canvas = await html2canvas(element, {
      scale: 2,
      useCORS: true,
      allowTaint: true,
      backgroundColor: '#ffffff'
    })
    
    const imgData = canvas.toDataURL('image/png')
    const pdf = new jsPDF()
    
    const imgWidth = 210 // A4 width in mm
    const pageHeight = 295 // A4 height in mm
    const imgHeight = (canvas.height * imgWidth) / canvas.width
    let heightLeft = imgHeight
    
    let position = 0
    
    pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
    heightLeft -= pageHeight
    
    while (heightLeft >= 0) {
      position = heightLeft - imgHeight
      pdf.addPage()
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
      heightLeft -= pageHeight
    }
    
    return pdf.output('blob')
  }

  private static async exportToSVG(element: HTMLElement): Promise<Blob> {
    // Convert DOM element to SVG
    const serializer = new XMLSerializer()
    const svgElements = element.querySelectorAll('svg')
    
    if (svgElements.length === 0) {
      throw new Error('No SVG elements found in the component')
    }
    
    // Take the first SVG element
    const svgString = serializer.serializeToString(svgElements[0])
    
    return new Blob([svgString], { type: 'image/svg+xml' })
  }

  private static async exportToCSV(data: any[]): Promise<Blob> {
    if (!data.length) {
      return new Blob([''], { type: 'text/csv' })
    }
    
    const headers = Object.keys(data[0])
    const csvRows = [
      headers.join(','),
      ...data.map(row => 
        headers.map(header => {
          const value = row[header]
          // Escape quotes and wrap in quotes if contains comma
          const escaped = String(value).replace(/"/g, '""')
          return escaped.includes(',') ? `"${escaped}"` : escaped
        }).join(',')
      )
    ]
    
    const csvString = csvRows.join('\n')
    return new Blob([csvString], { type: 'text/csv' })
  }

  private static async exportToJSON(data: any[]): Promise<Blob> {
    const jsonString = JSON.stringify(data, null, 2)
    return new Blob([jsonString], { type: 'application/json' })
  }

  private static async exportToExcel(data: any[]): Promise<Blob> {
    // This is a simplified version - in production you'd use a library like xlsx
    // For now, we'll export as CSV with Excel-friendly formatting
    return this.exportToCSV(data)
  }

  private static async generatePDFReport(
    template: ReportTemplate,
    widgets: DashboardWidget[],
    widgetElements: Map<string, HTMLElement>
  ): Promise<Blob> {
    const pdf = new jsPDF()
    let currentPage = 1
    let yPosition = 20
    
    // Add title page
    pdf.setFontSize(24)
    pdf.text(template.name, 20, yPosition)
    yPosition += 15
    
    if (template.description) {
      pdf.setFontSize(12)
      const splitDescription = pdf.splitTextToSize(template.description, 170)
      pdf.text(splitDescription, 20, yPosition)
      yPosition += splitDescription.length * 7
    }
    
    // Add generation info
    pdf.setFontSize(10)
    pdf.text(`Generated on: ${new Date().toLocaleDateString()}`, 20, yPosition + 10)
    yPosition += 30
    
    // Add each section
    for (const section of template.sections) {
      // Check if we need a new page
      if (section.pageBreak && currentPage > 1) {
        pdf.addPage()
        yPosition = 20
        currentPage++
      }
      
      // Section title
      pdf.setFontSize(18)
      pdf.text(section.title, 20, yPosition)
      yPosition += 10
      
      // Section description
      if (section.description) {
        pdf.setFontSize(10)
        const splitDesc = pdf.splitTextToSize(section.description, 170)
        pdf.text(splitDesc, 20, yPosition)
        yPosition += splitDesc.length * 5 + 10
      }
      
      // Add widgets for this section
      for (const widgetId of section.widgets) {
        const element = widgetElements.get(widgetId)
        if (element) {
          try {
            const canvas = await html2canvas(element, {
              scale: 1,
              useCORS: true,
              allowTaint: true,
              backgroundColor: '#ffffff'
            })
            
            const imgData = canvas.toDataURL('image/png')
            const imgWidth = 170
            const imgHeight = (canvas.height * imgWidth) / canvas.width
            
            // Check if image fits on current page
            if (yPosition + imgHeight > 280) {
              pdf.addPage()
              yPosition = 20
              currentPage++
            }
            
            pdf.addImage(imgData, 'PNG', 20, yPosition, imgWidth, imgHeight)
            yPosition += imgHeight + 15
            
          } catch (error) {
            console.error(`Error capturing widget ${widgetId}:`, error)
            // Add error placeholder
            pdf.setFontSize(10)
            pdf.text(`[Error rendering widget: ${widgetId}]`, 20, yPosition)
            yPosition += 10
          }
        }
      }
      
      yPosition += 10
    }
    
    // Add footer with page numbers
    const pageCount = pdf.internal.pages.length - 1
    for (let i = 1; i <= pageCount; i++) {
      pdf.setPage(i)
      pdf.setFontSize(8)
      pdf.text(`Page ${i} of ${pageCount}`, 185, 290)
    }
    
    return pdf.output('blob')
  }

  private static async generateExcelReport(
    template: ReportTemplate,
    widgets: DashboardWidget[]
  ): Promise<Blob> {
    // This would require a library like xlsx in production
    // For now, return a CSV representation
    const csvData = [
      ['Report Name', template.name],
      ['Generated On', new Date().toISOString()],
      [''],
      ['Sections', 'Widget Count'],
      ...template.sections.map(section => [
        section.title,
        section.widgets.length.toString()
      ])
    ]
    
    return this.exportToCSV(csvData.map(row => ({ 
      col1: row[0] || '', 
      col2: row[1] || '' 
    })))
  }

  /**
   * Download a blob as a file
   */
  static downloadBlob(blob: Blob, filename: string): void {
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  /**
   * Get appropriate file extension for export format
   */
  static getFileExtension(format: ExportFormat): string {
    switch (format) {
      case ExportFormat.PNG:
        return 'png'
      case ExportFormat.JPEG:
        return 'jpg'
      case ExportFormat.PDF:
        return 'pdf'
      case ExportFormat.SVG:
        return 'svg'
      case ExportFormat.CSV:
        return 'csv'
      case ExportFormat.JSON:
        return 'json'
      case ExportFormat.EXCEL:
        return 'xlsx'
      default:
        return 'file'
    }
  }

  /**
   * Generate filename with timestamp
   */
  static generateFilename(baseName: string, format: ExportFormat): string {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
    const extension = this.getFileExtension(format)
    return `${baseName}_${timestamp}.${extension}`
  }
}