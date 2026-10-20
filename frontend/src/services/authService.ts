import { UserAccount, UserProfile, UserRole } from '../types';
import { getDisplayName } from '../utils/language';

const CURRENT_USER_KEY = 'reanmore_auth_current_user_v1';
const ACCOUNTS_KEY = 'reanmore_auth_accounts_v1';
const TOKEN_KEY = 'reanmore_auth_token_v1';

export const DEFAULT_ACCOUNTS: UserAccount[] = [
  {
    id: 'account_student_sochea',
    username: 'sochea',
    role: 'student',
    pin: '1234',
    profile: {
      name: 'Sochea',
      grade: 4,
      subject: 'math',
      language: 'en',
      role: 'student',
    },
  },
  {
    id: 'account_parent_guardian',
    username: 'parent',
    role: 'parent',
    pin: '9999',
    profile: {
      name: 'Parent',
      grade: 4,
      subject: 'math',
      language: 'en',
      role: 'parent',
    },
  },
];

export class AuthService {
  private static listeners: Array<(account: UserAccount | null) => void> = [];

  static getToken(): string | null {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  }

  static setToken(token: string | null): void {
    try {
      if (token) {
        localStorage.setItem(TOKEN_KEY, token);
      } else {
        localStorage.removeItem(TOKEN_KEY);
      }
    } catch (err) {
      console.error('Failed to set token in localStorage:', err);
    }
  }

  static subscribe(callback: (account: UserAccount | null) => void): () => void {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter((cb) => cb !== callback);
    };
  }

  private static notify(account: UserAccount | null) {
    this.listeners.forEach((cb) => {
      try {
        cb(account);
      } catch (err) {
        console.error('Auth notify listener error:', err);
      }
    });
  }

  static getAccounts(): UserAccount[] {
    try {
      const raw = localStorage.getItem(ACCOUNTS_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed.map((acc: UserAccount) => ({
            ...acc,
            profile: {
              ...acc.profile,
              language: 'en' as const,
              name: getDisplayName(acc.profile?.name || '', false) || acc.profile?.name || 'Sochea',
            },
          }));
        }
      }
    } catch {}
    // Seed default accounts
    this.saveAccounts(DEFAULT_ACCOUNTS);
    return DEFAULT_ACCOUNTS;
  }

  static saveAccounts(accounts: UserAccount[]): void {
    try {
      localStorage.setItem(ACCOUNTS_KEY, JSON.stringify(accounts));
    } catch (err) {
      console.error('Failed to save accounts to localStorage:', err);
    }
  }

  static getCurrentUser(): UserAccount | null {
    try {
      const raw = localStorage.getItem(CURRENT_USER_KEY);
      if (raw === 'LOGGED_OUT') {
        return null;
      }
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && parsed.id) {
          return {
            ...parsed,
            profile: {
              ...parsed.profile,
              language: 'en' as const,
              name: getDisplayName(parsed.profile?.name || '', false) || parsed.profile?.name || 'Sochea',
            },
          };
        }
      }
      // If never visited/booted before, seed default user (sochea) once
      const hasBooted = localStorage.getItem('reanmore_auth_has_booted_v1');
      if (!hasBooted) {
        localStorage.setItem('reanmore_auth_has_booted_v1', 'true');
        const accounts = this.getAccounts();
        const defaultUser = accounts[0] || null;
        if (defaultUser) {
          localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(defaultUser));
          return defaultUser;
        }
      }
    } catch {}
    return null;
  }

  private static setCurrentUser(account: UserAccount | null): void {
    try {
      if (account) {
        localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(account));
      } else {
        localStorage.setItem(CURRENT_USER_KEY, 'LOGGED_OUT');
      }
    } catch (err) {
      console.error('Failed to set current user in localStorage:', err);
    }
    this.notify(account);
  }

  static login(
    identifier: string,
    pin?: string | undefined,
    skipPinCheck = false
  ): { success: boolean; account?: UserAccount | undefined; errorKhmer?: string | undefined; errorEng?: string | undefined } {
    const accounts = this.getAccounts();
    const cleanId = identifier.trim().toLowerCase();

    const account = accounts.find(
      (a) =>
        a.id.toLowerCase() === cleanId ||
        a.username.toLowerCase() === cleanId ||
        a.profile.name.toLowerCase().includes(cleanId)
    );

    if (!account) {
      return {
        success: false,
        errorKhmer: 'រកមិនឃើញគណនីនេះទេ។ សូមពិនិត្យឈ្មោះអ្នកប្រើឡើងវិញ។',
        errorEng: 'Account not found. Please check your username.',
      };
    }

    if (!skipPinCheck && account.pin) {
      if (pin === undefined || pin.trim() === '') {
        return {
          success: false,
          errorKhmer: 'សូមបញ្ចូលលេខកូដសម្ងាត់ (PIN)។',
          errorEng: 'Please enter PIN code.',
        };
      }
      // Normalize Khmer digits to Arabic digits (e.g. ១២៣៤ -> 1234)
      const normalizedPin = pin.trim().replace(/[០-៩]/g, (d) => String('០១២៣៤៥៦៧៨៩'.indexOf(d)));
      const expectedPin = account.pin.trim().replace(/[០-៩]/g, (d) => String('០១២៣៤៥៦៧៨៩'.indexOf(d)));

      if (normalizedPin !== expectedPin) {
        return {
          success: false,
          errorKhmer: `លេខកូដសម្ងាត់ (PIN) មិនត្រឹមត្រូវទេ។ (PIN ដើម: ${account.pin})`,
          errorEng: `Incorrect PIN code. (Default PIN: ${account.pin})`,
        };
      }
    }

    this.setCurrentUser(account);
    return { success: true, account };
  }

  static async loginRemote(
    classCode: string,
    studentName: string,
    pin: string
  ): Promise<{ success: boolean; account?: UserAccount | undefined; errorKhmer?: string | undefined; errorEng?: string | undefined }> {
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          class_code: classCode.trim().toUpperCase(),
          student_name: studentName.trim().toLowerCase(),
          pin: pin.trim(),
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        return {
          success: false,
          errorKhmer: data.detail || 'ការចូលបរាជ័យ (Login failed)',
          errorEng: data.detail || 'Login failed',
        };
      }

      if (data.token) {
        this.setToken(data.token);
      }

      const account: UserAccount = {
        id: data.user_id,
        username: data.student_name,
        role: data.role as UserRole,
        pin: pin.trim(),
        profile: {
          name: data.student_name,
          grade: (data.grade_level || 4) as any,
          subject: 'math',
          language: (data.language || 'km') as any,
          role: data.role as UserRole,
        },
      };

      const accounts = this.getAccounts();
      const existingIdx = accounts.findIndex((a) => a.id === account.id || a.username === account.username);
      if (existingIdx !== -1) {
        accounts[existingIdx] = account;
      } else {
        accounts.push(account);
      }
      this.saveAccounts(accounts);
      this.setCurrentUser(account);

      return { success: true, account };
    } catch (err) {
      console.warn('Remote login failed, falling back to local accounts:', err);
      return this.login(studentName, pin);
    }
  }

  static logout(): void {
    this.setToken(null);
    this.setCurrentUser(null);
  }

  static switchAccount(
    accountId: string,
    pin?: string | undefined
  ): { success: boolean; account?: UserAccount | undefined; errorKhmer?: string | undefined; errorEng?: string | undefined } {
    return this.login(accountId, pin);
  }

  static createAccount(
    username: string,
    role: UserRole,
    profileData: Partial<UserProfile>,
    pin?: string | undefined
  ): { success: boolean; account?: UserAccount | undefined; errorKhmer?: string | undefined; errorEng?: string | undefined } {
    const cleanUsername = username.trim().toLowerCase();
    if (!cleanUsername) {
      return {
        success: false,
        errorKhmer: 'សូមបញ្ចូលឈ្មោះអ្នកប្រើ។',
        errorEng: 'Please enter a username.',
      };
    }

    const accounts = this.getAccounts();
    if (accounts.some((a) => a.username.toLowerCase() === cleanUsername)) {
      return {
        success: false,
        errorKhmer: 'ឈ្មោះអ្នកប្រើនេះមានរួចហើយ។ សូមជ្រើសរើសឈ្មោះផ្សេង។',
        errorEng: 'Username already exists. Please pick another name.',
      };
    }

    const newAccount: UserAccount = {
      id: `account_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      username: cleanUsername,
      role,
      pin: pin ? pin.trim() : undefined,
      profile: {
        name: profileData.name || cleanUsername,
        grade: profileData.grade || 4,
        subject: profileData.subject || 'math',
        language: profileData.language || 'km',
        avatarUrl: profileData.avatarUrl,
        role,
      },
    };

    const updatedAccounts = [...accounts, newAccount];
    this.saveAccounts(updatedAccounts);
    this.setCurrentUser(newAccount);

    return { success: true, account: newAccount };
  }

  static updateProfile(updated: Partial<UserProfile>): UserAccount | null {
    const current = this.getCurrentUser();
    if (!current) return null;

    const updatedAccount: UserAccount = {
      ...current,
      profile: {
        ...current.profile,
        ...updated,
      },
    };

    const accounts = this.getAccounts().map((a) => (a.id === current.id ? updatedAccount : a));
    this.saveAccounts(accounts);
    this.setCurrentUser(updatedAccount);
    return updatedAccount;
  }
}
