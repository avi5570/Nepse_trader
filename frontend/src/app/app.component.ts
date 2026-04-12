import { HttpClient } from '@angular/common/http';
import { Component } from '@angular/core';

interface ApiMessage {
  title: string;
  text: string;
  count: number;
}

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  message: ApiMessage | null = null;
  loading = false;
  error = '';

  constructor(private http: HttpClient) {}

  fetchMessage() {
    this.loading = true;
    this.error = '';
    this.http.get<ApiMessage>('http://localhost:8000/api/message')
      .subscribe({
        next: data => {
          this.message = data;
          this.loading = false;
        },
        error: () => {
          this.error = 'Unable to connect to backend. Is the API running?';
          this.loading = false;
        }
      });
  }
}
