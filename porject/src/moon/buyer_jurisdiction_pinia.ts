import { defineStore } from 'pinia'


export const useBuyerJurisdictionStore = defineStore("buyerJurisdiction", {
    state: () => ({
        isJurisdiction: false
    }),
    actions:{
        setJurisdiction(value: string) {
            if (value === "admin"){
                this.isJurisdiction = true
            }else if(value === "user"){
                this.isJurisdiction = false
            }
            }
        }
    })
