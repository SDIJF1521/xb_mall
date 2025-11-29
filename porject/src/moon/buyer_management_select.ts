import { defineStore } from 'pinia'

export const useBuyerManagementSelectStore = defineStore("buyerManagementSelect", {
    state: () => ({
        to_uel: ""
    }),

    actions: {
        init() {
            // 从localStorage初始化值
            this.to_uel = localStorage.getItem('buyer_management_to_uel') || ""
        },

        setToUel(value: string) {
            this.to_uel = value
            localStorage.setItem('buyer_management_to_uel', value)
        },

        getToUel(): string {
            // 如果内存中没有值，从localStorage获取
            if (!this.to_uel) {
                this.to_uel = localStorage.getItem('buyer_management_to_uel') || ""
            }
            return this.to_uel
        },

        clearToUel() {
            this.to_uel = ""
            localStorage.removeItem('buyer_management_to_uel')
        }
    }
})
