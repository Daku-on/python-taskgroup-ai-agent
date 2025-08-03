/**
 * Interview scheduling page
 */

import { createFileRoute } from '@tanstack/react-router';
import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useAtom } from 'jotai';
import { addNotificationAtom } from '../stores/atoms';
import type { InterviewRequest, InterviewResponse, TimeSlot } from '../types/interview';
import { 
  Calendar,
  Clock, 
  Users, 
  Mail,
  Video,
  CheckCircle,
  XCircle,
  Plus,
  Minus,
  RefreshCw
} from 'lucide-react';
import { api } from '../api/client';

function InterviewsPage() {
  const [, addNotification] = useAtom(addNotificationAtom);
  
  const [interviewForm, setInterviewForm] = useState<InterviewRequest>({
    candidate_name: '',
    candidate_email: '',
    interviewer_names: [''],
    interviewer_emails: [''],
    duration_minutes: 60,
    auto_select: true
  });

  const [availableSlots, setAvailableSlots] = useState<TimeSlot[]>([]);
  const [showSlots, setShowSlots] = useState(false);

  // Interview scheduling mutation
  const scheduleInterviewMutation = useMutation({
    mutationFn: async (request: InterviewRequest) => {
      const response = await fetch('/api/interviews/schedule', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return response.json() as Promise<InterviewResponse>;
    },
    onSuccess: (result) => {
      if (result.status === 'scheduled') {
        addNotification({
          type: 'success',
          message: `面接が正常にスケジュールされました: ${result.scheduled_time}`
        });
        
        // フォームをリセット
        setInterviewForm({
          candidate_name: '',
          candidate_email: '',
          interviewer_names: [''],
          interviewer_emails: [''],
          duration_minutes: 60,
          auto_select: true
        });
      } else if (result.error) {
        addNotification({
          type: 'error',
          message: `面接スケジューリングに失敗しました: ${result.error}`
        });
      }
    },
    onError: (error: any) => {
      addNotification({
        type: 'error',
        message: `エラー: ${error.message || '面接スケジューリングに失敗しました'}`
      });
    }
  });

  // Available slots query
  const fetchAvailableSlots = async () => {
    if (!interviewForm.candidate_email || interviewForm.interviewer_emails.some(email => !email)) {
      throw new Error('候補者と面接官のメールアドレスを入力してください');
    }

    const params = new URLSearchParams({
      candidate_email: interviewForm.candidate_email,
      interviewer_emails: interviewForm.interviewer_emails.filter(email => email).join(','),
      duration_minutes: interviewForm.duration_minutes?.toString() || '60',
      days_ahead: '7'
    });

    const response = await fetch(`/api/interviews/available-slots?${params}`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    return data.available_slots as TimeSlot[];
  };

  const availableSlotsQuery = useQuery({
    queryKey: ['available-slots', interviewForm.candidate_email, interviewForm.interviewer_emails],
    queryFn: fetchAvailableSlots,
    enabled: false, // Manual trigger only
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!interviewForm.candidate_name || !interviewForm.candidate_email) {
      addNotification({
        type: 'error',
        message: '候補者名とメールアドレスは必須です'
      });
      return;
    }

    if (interviewForm.interviewer_emails.some(email => !email)) {
      addNotification({
        type: 'error',
        message: 'すべての面接官のメールアドレスを入力してください'
      });
      return;
    }

    scheduleInterviewMutation.mutate(interviewForm);
  };

  const handleFindSlots = async () => {
    try {
      const slots = await fetchAvailableSlots();
      setAvailableSlots(slots);
      setShowSlots(true);
      
      if (slots.length === 0) {
        addNotification({
          type: 'warning',
          message: '指定期間に利用可能な時間枠が見つかりませんでした'
        });
      }
    } catch (error: any) {
      addNotification({
        type: 'error',
        message: `空き時間検索エラー: ${error.message}`
      });
    }
  };

  const addInterviewer = () => {
    setInterviewForm(prev => ({
      ...prev,
      interviewer_names: [...prev.interviewer_names, ''],
      interviewer_emails: [...prev.interviewer_emails, '']
    }));
  };

  const removeInterviewer = (index: number) => {
    if (interviewForm.interviewer_names.length > 1) {
      setInterviewForm(prev => ({
        ...prev,
        interviewer_names: prev.interviewer_names.filter((_, i) => i !== index),
        interviewer_emails: prev.interviewer_emails.filter((_, i) => i !== index)
      }));
    }
  };

  const updateInterviewer = (index: number, field: 'name' | 'email', value: string) => {
    setInterviewForm(prev => ({
      ...prev,
      [field === 'name' ? 'interviewer_names' : 'interviewer_emails']: 
        field === 'name' 
          ? prev.interviewer_names.map((item, i) => i === index ? value : item)
          : prev.interviewer_emails.map((item, i) => i === index ? value : item)
    }));
  };

  const formatDateTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleString('ja-JP', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      weekday: 'long',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="px-4 py-6 sm:px-0">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">面接スケジューリング</h1>
        <p className="mt-2 text-gray-600">
          完全自動化された面接日程調整システム
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
        {/* Interview Scheduling Form */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
            <Calendar className="w-5 h-5 mr-2" />
            面接スケジュール作成
          </h2>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Candidate Information */}
            <div className="border-b border-gray-200 pb-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">候補者情報</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="candidateName" className="block text-sm font-medium text-gray-700 mb-2">
                    候補者名 *
                  </label>
                  <input
                    id="candidateName"
                    type="text"
                    value={interviewForm.candidate_name}
                    onChange={(e) => setInterviewForm({...interviewForm, candidate_name: e.target.value})}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="田中太郎"
                    required
                  />
                </div>
                
                <div>
                  <label htmlFor="candidateEmail" className="block text-sm font-medium text-gray-700 mb-2">
                    メールアドレス *
                  </label>
                  <input
                    id="candidateEmail"
                    type="email"
                    value={interviewForm.candidate_email}
                    onChange={(e) => setInterviewForm({...interviewForm, candidate_email: e.target.value})}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="tanaka@example.com"
                    required
                  />
                </div>
              </div>
            </div>

            {/* Interviewers */}
            <div className="border-b border-gray-200 pb-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900 flex items-center">
                  <Users className="w-5 h-5 mr-2" />
                  面接官
                </h3>
                <button
                  type="button"
                  onClick={addInterviewer}
                  className="flex items-center px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200"
                >
                  <Plus className="w-4 h-4 mr-1" />
                  追加
                </button>
              </div>

              <div className="space-y-3">
                {interviewForm.interviewer_names.map((name, index) => (
                  <div key={index} className="flex items-center space-x-3">
                    <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-3">
                      <input
                        type="text"
                        value={name}
                        onChange={(e) => updateInterviewer(index, 'name', e.target.value)}
                        className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        placeholder="面接官名"
                      />
                      <input
                        type="email"
                        value={interviewForm.interviewer_emails[index]}
                        onChange={(e) => updateInterviewer(index, 'email', e.target.value)}
                        className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        placeholder="interviewer@company.com"
                        required
                      />
                    </div>
                    
                    {interviewForm.interviewer_names.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeInterviewer(index)}
                        className="flex-shrink-0 p-2 text-red-600 hover:text-red-800"
                      >
                        <Minus className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Interview Settings */}
            <div className="border-b border-gray-200 pb-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                <Clock className="w-5 h-5 mr-2" />
                面接設定
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="duration" className="block text-sm font-medium text-gray-700 mb-2">
                    面接時間（分）
                  </label>
                  <select
                    id="duration"
                    value={interviewForm.duration_minutes}
                    onChange={(e) => setInterviewForm({...interviewForm, duration_minutes: parseInt(e.target.value)})}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value={30}>30分</option>
                    <option value={45}>45分</option>
                    <option value={60}>60分</option>
                    <option value={90}>90分</option>
                    <option value={120}>120分</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    スケジューリング方式
                  </label>
                  <div className="space-y-2">
                    <label className="flex items-center">
                      <input
                        type="radio"
                        checked={interviewForm.auto_select}
                        onChange={() => setInterviewForm({...interviewForm, auto_select: true})}
                        className="mr-2"
                      />
                      <span className="text-sm">自動選択（推奨）</span>
                    </label>
                    <label className="flex items-center">
                      <input
                        type="radio"
                        checked={!interviewForm.auto_select}
                        onChange={() => setInterviewForm({...interviewForm, auto_select: false})}
                        className="mr-2"
                      />
                      <span className="text-sm">手動選択</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex space-x-4">
              <button
                type="button"
                onClick={handleFindSlots}
                disabled={availableSlotsQuery.isLoading}
                className="flex items-center px-4 py-2 border border-blue-600 text-blue-600 rounded-md hover:bg-blue-50 disabled:opacity-50"
              >
                {availableSlotsQuery.isLoading ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Calendar className="w-4 h-4 mr-2" />
                )}
                空き時間を確認
              </button>

              <button
                type="submit"
                disabled={scheduleInterviewMutation.isPending}
                className="flex items-center px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {scheduleInterviewMutation.isPending ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Video className="w-4 h-4 mr-2" />
                )}
                面接をスケジュール
              </button>
            </div>
          </form>
        </div>

        {/* Available Slots */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
            <Clock className="w-5 h-5 mr-2" />
            利用可能な時間枠
          </h2>

          {!showSlots ? (
            <div className="text-center py-12 text-gray-500">
              <Calendar className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>空き時間を確認ボタンを押すと</p>
              <p>利用可能な時間枠が表示されます</p>
            </div>
          ) : availableSlotsQuery.isLoading ? (
            <div className="text-center py-12">
              <RefreshCw className="w-8 h-8 mx-auto mb-4 animate-spin text-blue-600" />
              <p className="text-gray-600">空き時間を検索中...</p>
            </div>
          ) : availableSlots.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <XCircle className="w-12 h-12 mx-auto mb-4 text-red-400" />
              <p>指定期間に利用可能な時間枠が</p>
              <p>見つかりませんでした</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {availableSlots.map((slot, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-gray-900">
                        {formatDateTime(slot.start)}
                      </div>
                      <div className="text-sm text-gray-500">
                        {new Date(slot.end).toLocaleTimeString('ja-JP', {
                          hour: '2-digit',
                          minute: '2-digit'
                        })} まで
                      </div>
                      <div className="text-xs text-gray-400 mt-1">
                        参加者: {slot.attendees.length}名
                      </div>
                    </div>
                    
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* System Features */}
      <div className="mt-8 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">🤖 自動化機能</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="flex items-center space-x-2">
            <Calendar className="w-5 h-5 text-blue-600" />
            <span className="text-sm text-gray-700">カレンダー自動チェック</span>
          </div>
          <div className="flex items-center space-x-2">
            <Video className="w-5 h-5 text-green-600" />
            <span className="text-sm text-gray-700">Google Meet自動予約</span>
          </div>
          <div className="flex items-center space-x-2">
            <Mail className="w-5 h-5 text-purple-600" />
            <span className="text-sm text-gray-700">招待メール自動送信</span>
          </div>
          <div className="flex items-center space-x-2">
            <Users className="w-5 h-5 text-orange-600" />
            <span className="text-sm text-gray-700">複数参加者対応</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export const Route = createFileRoute('/interviews')({
  component: InterviewsPage,
});