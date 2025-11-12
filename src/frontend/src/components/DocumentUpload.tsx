import React, { useState, useEffect, useCallback, useId } from 'react';
import { Upload, FileText, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { api } from '../services/api';
import type { Document, DocumentType } from '../types';

interface DocumentUploadProps {
  sessionId: string;
  onUploadComplete?: (document: Document) => void;
  onDocumentsChange?: (documents: Document[]) => void;
}

const DOCUMENT_OPTIONS: { value: DocumentType; label: string }[] = [
  { value: 'w2', label: 'W-2 Form' },
  { value: '1099', label: '1099 Form' },
  { value: 'portfolio', label: 'Portfolio PDF' },
];

export default function DocumentUpload({
  sessionId,
  onUploadComplete,
  onDocumentsChange,
}: DocumentUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [uploadedDocs, setUploadedDocs] = useState<Document[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [documentsError, setDocumentsError] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<DocumentType>('w2');
  const fileInputId = useId();

  const refreshDocuments = useCallback(async () => {
    setLoadingDocs(true);
    try {
      const context = await api.getSessionContext(sessionId);
      const docs = context.documents || [];
      setDocumentsError(null);
      setUploadedDocs(docs);
    } catch (err: any) {
      console.error('Failed to load documents:', err);
      setDocumentsError('Unable to load uploaded documents. Please try again.');
    } finally {
      setLoadingDocs(false);
    }
  }, [sessionId]);

  useEffect(() => {
    refreshDocuments();
  }, [refreshDocuments]);

  useEffect(() => {
    onDocumentsChange?.(uploadedDocs);
  }, [uploadedDocs, onDocumentsChange]);

  const uploadDocument = async (type: DocumentType, file: File) => {
    switch (type) {
      case 'w2':
        return api.uploadW2(sessionId, file);
      case '1099':
        return api.upload1099(sessionId, file);
      case 'portfolio':
        return api.uploadPortfolio(sessionId, file);
      default:
        throw new Error(`Unsupported document type: ${type}`);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    console.log('File selected:', file);

    if (!file) {
      console.log('No file selected');
      return;
    }

    console.log('File type:', file.type);
    console.log('File size:', file.size);

    if (file.type !== 'application/pdf') {
      setError('Please upload a PDF file');
      console.error('Invalid file type:', file.type);
      return;
    }

    console.log('Starting upload for session:', sessionId);
    console.log('Document type:', selectedType);

    setUploading(true);
    setError(null);

    try {
      const document = await uploadDocument(selectedType, file);

      console.log('Upload successful:', document);
      await refreshDocuments();
      onUploadComplete?.(document);
      e.target.value = ''; // Reset file input
    } catch (err: any) {
      console.error('Upload error:', err);
      console.error('Error details:', {
        message: err.message,
        response: err.response?.data,
        status: err.response?.status,
      });
      setError(err.response?.data?.detail || 'Failed to upload document. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <FileText className="w-6 h-6 text-primary-600" />
        <h3 className="text-xl font-bold">Upload Tax Documents</h3>
      </div>

      <p className="text-sm text-gray-600 mb-4">
        Upload your W-2, 1099, or portfolio PDFs to get personalized financial insights and answers.
      </p>

      <div className="mb-4">
        <label className="block text-sm font-semibold text-gray-700 mb-2">Document Type</label>
        <div className="flex flex-wrap gap-4">
          {DOCUMENT_OPTIONS.map((option) => (
            <label key={option.value} className="flex items-center">
              <input
                type="radio"
                name="docType"
                value={option.value}
                checked={selectedType === option.value}
                onChange={() => setSelectedType(option.value)}
                className="mr-2"
                disabled={uploading}
              />
              <span className="text-sm">{option.label}</span>
            </label>
          ))}
        </div>
      </div>

      <label className="block" htmlFor={fileInputId}>
        <input
          type="file"
          accept=".pdf"
          onChange={handleFileUpload}
          disabled={uploading}
          className="hidden"
          id={fileInputId}
        />
        <div
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
            uploading
              ? 'border-gray-300 bg-gray-50 cursor-not-allowed'
              : 'border-primary-300 hover:border-primary-500 hover:bg-primary-50'
          }`}
        >
          {uploading ? (
            <div className="flex flex-col items-center">
              <Loader2 className="w-12 h-12 text-primary-600 animate-spin mb-2" />
              <p className="text-sm text-gray-600">Uploading and processing document...</p>
            </div>
          ) : (
            <div className="flex flex-col items-center">
              <Upload className="w-12 h-12 text-primary-600 mb-2" />
              <p className="text-sm font-semibold text-gray-700 mb-1">
                Click to upload {selectedType.toUpperCase()} form
              </p>
              <p className="text-xs text-gray-500">PDF files only</p>
            </div>
          )}
        </div>
      </label>

      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      <div className="mt-4">
        <p className="text-sm font-semibold text-gray-700 mb-2">Uploaded Documents:</p>
        {loadingDocs ? (
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Loader2 className="w-4 h-4 animate-spin" />
            Loading documents...
          </div>
        ) : documentsError ? (
          <div className="text-sm text-red-600">{documentsError}</div>
        ) : uploadedDocs.length === 0 ? (
          <p className="text-sm text-gray-500">No documents uploaded yet.</p>
        ) : (
          <div className="space-y-2">
            {uploadedDocs.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg"
              >
                <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">
                    {doc.document_type?.toString().toUpperCase()}
                  </p>
                  <p className="text-xs text-gray-500">
                    Uploaded {new Date(doc.created_at).toLocaleString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
