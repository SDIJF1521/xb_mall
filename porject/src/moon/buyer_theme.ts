export default class BuyerTheme{
    toggleTheme(isDark: boolean){
        if(isDark){
            document.documentElement.classList.add('dark')
        }else{
            document.documentElement.classList.remove('dark')
        }
    }

    // 从 localStorage 读取并应用已保存的卖家端主题，无记录则默认暗色
    initTheme(){
        const saved = localStorage.getItem('buyer_theme')
        this.toggleTheme(saved === null ? true : saved === 'dark')
    }
}