import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';

interface ApiMessage {
  title: string;
  text: string;
  count: number;
}

interface UploadResponse {
  message: string;
  files_processed: number;
  records_inserted: number;
  records_updated: number;
}

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  message: ApiMessage | null = null;
  loading = false;
  error = '';
  isAuthenticated = false;

  selectedFiles: File[] = [];
  uploading = false;
  uploadResult: UploadResponse | null = null;
  uploadError = '';

  constructor(private http: HttpClient) {}

  ngOnInit() {
    // Check for token in URL parameters (from login redirect)
    const urlParams = new URLSearchParams(window.location.search);
    const tokenFromUrl = urlParams.get('token');

    if (tokenFromUrl) {
      // Store the token from URL
      localStorage.setItem('access_token', tokenFromUrl);
      console.log('Token from URL stored:', tokenFromUrl);
      // Clean up the URL
      window.history.replaceState({}, document.title, window.location.pathname);
    }

    // Check if user is authenticated
    const token = localStorage.getItem('access_token');
    console.log('Token from localStorage:', token);
    this.isAuthenticated = !!token;
    console.log('Is authenticated:', this.isAuthenticated);

    if (this.isAuthenticated) {
      this.fetchMessage();
    }
  }

  private getHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token');
    return new HttpHeaders({
      'Authorization': `Bearer ${token}`
    });
  }

  fetchMessage() {
    if (!this.isAuthenticated) {
      this.error = 'Please log in to access the application.';
      return;
    }

    this.loading = true;
    this.error = '';
    this.http.get<ApiMessage>('http://localhost:8000/api/message', { headers: this.getHeaders() })
      .subscribe({
        next: data => {
          this.message = data;
          this.loading = false;
        },
        error: (error) => {
          if (error.status === 401) {
            // Token expired or invalid, redirect to login
            this.logout();
          } else {
            this.error = 'Unable to connect to backend. Is the API running?';
            this.loading = false;
          }
        }
      });
  }

  onFileSelected(event: any) {
    this.selectedFiles = Array.from(event.target.files);
    this.uploadResult = null;
    this.uploadError = '';
  }

  uploadFiles() {
    if (this.selectedFiles.length === 0) {
      return;
    }

    this.uploading = true;
    this.uploadError = '';
    this.uploadResult = null;

    const formData = new FormData();
    this.selectedFiles.forEach(file => {
      formData.append('files', file);
    });

    this.http.post<UploadResponse>('http://localhost:8000/upload-csv', formData, {
      headers: this.getHeaders()
    }).subscribe({
      next: (result) => {
        this.uploadResult = result;
        this.uploading = false;
        this.selectedFiles = [];
        // Clear the file input
        const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
        if (fileInput) {
          fileInput.value = '';
        }
      },
      error: (error) => {
        if (error.status === 401) {
          this.logout();
        } else {
          this.uploadError = error.error?.detail || 'Upload failed. Please try again.';
          this.uploading = false;
        }
      }
    });
  }

  logout() {
    localStorage.removeItem('access_token');
    this.isAuthenticated = false;
    this.message = null;
    this.error = '';
    this.selectedFiles = [];
    this.uploadResult = null;
    this.uploadError = '';
    // Redirect to login page
    window.location.href = 'http://localhost:8000/login';
  }
}
