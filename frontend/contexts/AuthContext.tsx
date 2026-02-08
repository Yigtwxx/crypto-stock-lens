'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { User, Session, AuthChangeEvent } from '@supabase/supabase-js'
import { getSupabase } from '@/lib/supabase'

interface AuthContextType {
    user: User | null
    session: Session | null
    loading: boolean
    signIn: (email: string, password: string) => Promise<{ error: Error | null }>
    signUp: (email: string, password: string) => Promise<{ error: Error | null }>
    signOut: () => Promise<void>
    signInWithGoogle: () => Promise<{ error: Error | null }>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null)
    const [session, setSession] = useState<Session | null>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const supabase = getSupabase()

        // Get initial session
        supabase.auth.getSession().then(({ data: { session: initialSession } }) => {
            setSession(initialSession)
            setUser(initialSession?.user ?? null)
            setLoading(false)
        })

        // Listen for auth changes
        const { data: { subscription } } = supabase.auth.onAuthStateChange(
            (event: AuthChangeEvent, newSession: Session | null) => {
                setSession(newSession)
                setUser(newSession?.user ?? null)
                setLoading(false)
            }
        )

        return () => subscription.unsubscribe()
    }, [])

    const signIn = async (email: string, password: string) => {
        const supabase = getSupabase()
        const { error } = await supabase.auth.signInWithPassword({ email, password })
        return { error }
    }

    const signUp = async (email: string, password: string) => {
        const supabase = getSupabase()
        const { error } = await supabase.auth.signUp({ email, password })
        return { error }
    }

    const signOut = async () => {
        const supabase = getSupabase()
        await supabase.auth.signOut()
    }

    const signInWithGoogle = async () => {
        const supabase = getSupabase()
        const { error } = await supabase.auth.signInWithOAuth({
            provider: 'google',
            options: {
                redirectTo: `${window.location.origin}/auth/callback`
            }
        })
        return { error }
    }

    return (
        <AuthContext.Provider value={{
            user,
            session,
            loading,
            signIn,
            signUp,
            signOut,
            signInWithGoogle
        }}>
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    const context = useContext(AuthContext)
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider')
    }
    return context
}
