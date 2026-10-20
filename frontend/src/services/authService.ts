import { UserAccount, UserProfile, UserRole } from '../types';
import { getDisplayName } from '../utils/language';

const CURRENT_USER_KEY = 'reanmore_auth_current_user_v1';
const ACCOUNTS_KEY = 'reanmore_auth_accounts_v1';
const TOKEN_KEY = 'reanmore_auth_token_v1';

export const DEFAULT_ACCOUNTS: UserAccount[] = [];

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
              name: getDisplayName(acc.profile?.name || '', false) || acc.profile?.name || 'Learner',
            },
          }));
        }
      }
    } catch {}
    return [];
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
              name: getDisplayName(parsed.profile?.name || '', false) || parsed.profile?.name || 'Learner',
            },
          };
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
    identifier: string,
    pin: string,
    classCode: string = 'MAIN'
  ): Promise<{ success: boolean; account?: UserAccount | undefined; errorKhmer?: string | undefined; errorEng?: string | undefined }> {
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          identifier: identifier.trim(),
          pin: pin.trim(),
          class_code: (classCode || 'MAIN').trim().toUpperCase(),
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

      const idCard = data.id_card || data.user_id;
      const accounts = this.getAccounts();
      const existing = accounts.find(
        (a) =>
          a.username.toLowerCase() === data.student_name.toLowerCase() ||
          (a.idCard && a.idCard.toLowerCase() === idCard.toLowerCase())
      );

      const account: UserAccount = {
        id: data.user_id,
        username: data.student_name,
        role: data.role as UserRole,
        pin: pin.trim(),
        idCard,
        profile: {
          name: existing?.profile.name || data.student_name,
          grade: (data.grade_level || 4) as any,
          subject: 'math',
          language: (data.language || 'en') as any,
          role: data.role as UserRole,
          avatarUrl: existing?.profile.avatarUrl || '👦',
          idCard,
        },
      };

      const existingIdx = accounts.findIndex(
        (a) => a.id === account.id || a.username === account.username || (a.idCard && a.idCard === idCard)
      );
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
      return this.login(identifier, pin);
    }
  }

  static async registerRemote(
    studentName: string,
    pin: string,
    gradeLevel: number = 4,
    role: UserRole = 'student',
    language: string = 'en',
    avatarUrl: string = '👦',
    customIdCard?: string,
    classCode: string = 'MAIN'
  ): Promise<{ success: boolean; account?: UserAccount | undefined; errorKhmer?: string | undefined; errorEng?: string | undefined }> {
    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_name: studentName.trim(),
          pin: pin.trim(),
          grade_level: gradeLevel,
          role,
          language,
          id_card: customIdCard?.trim() || undefined,
          class_code: (classCode || 'MAIN').trim().toUpperCase(),
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        return {
          success: false,
          errorKhmer: data.detail || 'ការចុះឈ្មោះបរាជ័យ (Registration failed)',
          errorEng: data.detail || 'Registration failed',
        };
      }

      if (data.token) {
        this.setToken(data.token);
      }

      const idCard = data.id_card || data.user_id;

      const account: UserAccount = {
        id: data.user_id,
        username: data.student_name,
        role: data.role as UserRole,
        pin: pin.trim(),
        idCard,
        profile: {
          name: studentName.trim(),
          grade: (data.grade_level || gradeLevel) as any,
          subject: 'math',
          language: (data.language || 'en') as any,
          role: data.role as UserRole,
          avatarUrl: avatarUrl || '👦',
          idCard,
        },
      };

      const accounts = this.getAccounts();
      const existingIdx = accounts.findIndex(
        (a) => a.id === account.id || a.username === account.username || (a.idCard && a.idCard === idCard)
      );
      if (existingIdx !== -1) {
        accounts[existingIdx] = account;
      } else {
        accounts.push(account);
      }
      this.saveAccounts(accounts);
      this.setCurrentUser(account);

      return { success: true, account };
    } catch (err) {
      console.warn('Remote register failed, falling back to local account:', err);
      const randomId = `RM-${Math.floor(10000 + Math.random() * 90000)}`;
      return this.createAccount(
        studentName,
        role,
        {
          name: studentName,
          grade: gradeLevel as any,
          subject: 'math',
          language: language as any,
          role,
          avatarUrl,
          idCard: randomId,
        },
        pin
      );
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
